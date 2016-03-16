import base64
import hashlib
import os
import subprocess
from urlparse import urlparse


def download_url(url, work_dir='.', name=None, s3_encryption_key_path=None):
    """
    Downloads URL, can pass in file://, http://, s3://, or ftp://

    :param str url: URL to download from
    :param str work_dir: Directory to download file to
    :param str name: Name of output file, if None, basename of URL is used
    :param str s3_encryption_key_path: Path to the 32-byte encryption key if stored in S3
    :return str: Path to the downloaded file
    """
    file_path = os.path.join(work_dir, name) if name else os.path.join(work_dir, os.path.basename(url))
    if s3_encryption_key_path:
        _download_encrypted_file(url, file_path, s3_encryption_key_path)
    elif url.startswith('s3:'):
        _download_s3_url(file_path, url)
    else:
        subprocess.check_call(['curl', '-fs', '--retry', '5', '--create-dir', url, '-o', file_path])
    assert os.path.exists(file_path)
    return file_path


def download_url_job(job, url, name=None, s3_encryption_key_path=None):
    """Job version of `download_url`"""
    work_dir = job.fileStore.getLocalTempDir()
    fpath = download_url(url, work_dir=work_dir, name=name, s3_encryption_key_path=s3_encryption_key_path)
    return job.fileStore.writeGlobalFile(fpath)


def s3am_upload(fpath, s3_dir, num_cores=1, s3_encryption_key_path=None):
    """
    Uploads a file to s3 via S3AM
    For SSE-C encryption: provide a path to a 32-byte file

    :param str fpath: Path to file to upload
    :param str s3_dir: Ouptut S3 path. Format: s3://bucket/[directory]
    :param int num_cores: Number of cores to use for up/download with S3AM
    :param str s3_encryption_key_path: (OPTIONAL) Path to 32-byte key to be used for SSE-C encryption
    """
    assert s3_dir.startswith('s3://'), 'Format of s3_dir (s3://) is incorrect: {}'.format(s3_dir)
    s3_dir = os.path.join(s3_dir, os.path.basename(fpath))
    if s3_encryption_key_path:
        base_url = 'https://s3-us-west-2.amazonaws.com/'
        url = os.path.join(base_url, s3_dir[5:])
        temp_key_path = os.path.join(os.path.split(fpath)[0], 'temp.key')
        with open(temp_key_path, 'wb') as f_out:
            f_out.write(_generate_unique_key(s3_encryption_key_path, url))
        _s3am_with_retry(num_cores, '--sse-key-file', temp_key_path,
                         'file://{}'.format(fpath), s3_dir)
    else:
        _s3am_with_retry(num_cores, 'file://{}'.format(fpath), s3_dir)


def s3am_upload_job(job, file_id, file_name, s3_dir, num_cores, s3_encryption_key_path=None):
    """Job version of `s3am_upload`"""
    work_dir = job.fileStore.getLocalTempDir()
    fpath = job.fileStore.readGlobalFile(file_id, os.path.join(work_dir, file_name))
    s3am_upload(fpath=fpath, s3_dir=s3_dir, num_cores=num_cores, s3_encryption_key_path=s3_encryption_key_path)


def _download_s3_url(file_path, url):
    """
    Downloads from S3 URL via Boto

    :param str file_path: Path to file
    :param str url: S3 URL
    """
    from boto.s3.connection import S3Connection
    s3 = S3Connection()
    try:
        parsed_url = urlparse(url)
        if not parsed_url.netloc or not parsed_url.path.startswith('/'):
            raise RuntimeError("An S3 URL must be of the form s3:/BUCKET/ or "
                               "s3://BUCKET/KEY. '%s' is not." % url)
        bucket = s3.get_bucket(parsed_url.netloc)
        key = bucket.get_key(parsed_url.path[1:])
        key.get_contents_to_filename(file_path)
    finally:
        s3.close()


def _download_encrypted_file(url, file_path, key_path):
    """
    Downloads encrypted files from S3

    :param str url: URL to be downloaded
    :param str file_path: Output path to file
    :param str key_path: Path to the 32-byte key file
    """
    # Grab master key
    with open(key_path, 'r') as f:
        key = f.read()
    if len(key) != 32:
        raise RuntimeError('Invalid Key! Must be 32 bytes: {}'.format(key))

    key = _generate_unique_key(key_path, url)
    # Create necessary headers for SSE-C encryption and download
    encoded_key = base64.b64encode(key)
    encoded_key_md5 = base64.b64encode(hashlib.md5(key).digest())
    h1 = 'x-amz-server-side-encryption-customer-algorithm:AES256'
    h2 = 'x-amz-server-side-encryption-customer-key:{}'.format(encoded_key)
    h3 = 'x-amz-server-side-encryption-customer-key-md5:{}'.format(encoded_key_md5)
    subprocess.check_call(['curl', '-fs', '--retry', '5', '-H', h1, '-H', h2, '-H', h3, url, '-o', file_path])
    assert os.path.exists(file_path)


def _generate_unique_key(master_key_path, url):
    """
    Generate a unique encryption key given a URL and a path to another "master" encrypion key

    :param str master_key_path: Path to the master key
    :param str url: URL used to generate unique encryption key
    :return str: The new 32-byte key
    """
    with open(master_key_path, 'r') as f:
        master_key = f.read()
    assert len(master_key) == 32, 'Invalid Key! Must be 32 characters. ' \
                                  'Key: {}, Length: {}'.format(master_key, len(master_key))
    new_key = hashlib.sha256(master_key + url).digest()
    assert len(new_key) == 32, 'New key is invalid and is not 32 characters: {}'.format(new_key)
    return new_key


def _s3am_with_retry(c, *args):
    """
    Calls S3AM upload with retries

    :param int c: Number of cores to pass to upload/download slots
    :param list[str] args: Additional arguments to append to s3am
    """
    retry_count = 3
    for i in xrange(retry_count):
        s3am_command = ['s3am', 'upload', '--resume', '--part-size=50M',
                        '--upload-slots={}'.format(c),
                        '--download-slots={}'.format(c)] + list(args)
        ret_code = subprocess.call(s3am_command)
        if ret_code == 0:
            return
        else:
            print 'S3AM failed with status code: {}'.format(ret_code)
    raise RuntimeError('S3AM failed to upload after {} retries.'.format(retry_count))
