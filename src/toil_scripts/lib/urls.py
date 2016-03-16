import base64
import hashlib
import os
import subprocess
from urlparse import urlparse


def download_encrypted_file_job(job, url, key_path):
    """
    Downloads encrypted files from S3 via header injection

    url: str            URL to be downloaded
    key_path: str       Path to key file
    name: str           Symbolic name associated with file
    """
    work_dir = job.fileStore.getLocalTempDir()
    file_path = os.path.join(work_dir, os.path.basename(url))
    # Grab master key
    with open(key_path, 'r') as f:
        key = f.read()
    if len(key) != 32:
        raise RuntimeError('Invalid Key! Must be 32 bytes: {}'.format(key))

    key = generate_unique_key(key_path, url)
    # Create necessary headers for SSE-C encryption and download
    encoded_key = base64.b64encode(key)
    encoded_key_md5 = base64.b64encode(hashlib.md5(key).digest())
    h1 = 'x-amz-server-side-encryption-customer-algorithm:AES256'
    h2 = 'x-amz-server-side-encryption-customer-key:{}'.format(encoded_key)
    h3 = 'x-amz-server-side-encryption-customer-key-md5:{}'.format(encoded_key_md5)
    try:
        subprocess.check_call(['curl', '-fs', '--retry', '5', '-H', h1, '-H', h2, '-H', h3, url, '-o', file_path])
    except OSError:
        raise RuntimeError('Failed to find "curl". Install via "apt-get install curl"')
    assert os.path.exists(file_path)
    return job.fileStore.writeGlobalFile(file_path)


def download_from_url_job(job, url):
    """
    Download a file given a URL

    url: str    URL to download
    """
    work_dir = job.fileStore.getLocalTempDir()
    file_path = os.path.join(work_dir, os.path.basename(url))
    if url.startswith('s3:'):
        download_from_s3_url(file_path, url)
    else:
        try:
            subprocess.check_call(['curl', '-fs', '--retry', '5', '--create-dir', url, '-o', file_path])
        except OSError:
            raise RuntimeError('Failed to find "curl". Install via "apt-get install curl"')
    assert os.path.exists(file_path)
    return job.fileStore.writeGlobalFile(file_path)


def s3am_upload_job(job, file_id, s3_dir, num_cores, file_name, key_path=None):
    """
    Uploads a file to S3 via S3AM.
    For SSE-C encryption: provide a path to a 32-byte file

    id: str             ID of file to be uploaded
    s3_dir: str         S3 path. Format: s3://bucket/[directory]/file
    cores: int/str      Number of cores on worker
    key_path: str       (OPTIONAL) Path to 32-byte key to be used for SSE-C encryption
    """
    def s3am_with_retry(c, *args):
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

    assert s3_dir.startswith('s3://'), 'Format of s3_dir (s3://) is incorrect: {}'.format(s3_dir)
    s3_dir = os.path.join(s3_dir, file_name)
    work_dir = job.fileStore.getLocalTempDir()
    fpath = job.fileStore.readGlobalFile(file_id, os.path.join(work_dir, file_name))
    # Generate keyfile for upload
    if key_path:
        base_url = 'https://s3-us-west-2.amazonaws.com/'
        url = os.path.join(base_url, s3_dir[5:])
        with open(os.path.join(work_dir, 'temp.key'), 'wb') as f_out:
            f_out.write(generate_unique_key(key_path, url))
        s3am_with_retry(num_cores, '--sse-key-file', os.path.join(work_dir, 'temp.key'),
                        'file://{}'.format(fpath), s3_dir)
    else:
        s3am_with_retry(num_cores, 'file://{}'.format(fpath), s3_dir)


def download_from_url(url, work_dir='.', name=None):
    """
    Download a file given a URL

    url: str    URL to download
    """
    file_path = os.path.join(work_dir, name) if name else os.path.join(work_dir, os.path.basename(url))
    if url.startswith('s3:'):
        download_from_s3_url(file_path, url)
    else:
        try:
            subprocess.check_call(['curl', '-fs', '--retry', '5', '--create-dir', url, '-o', file_path])
        except OSError:
            raise RuntimeError('Failed to find "curl". Install via "apt-get install curl"')
    assert os.path.exists(file_path)


def download_from_s3_url(file_path, url):
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


def generate_unique_key(master_key_path, url):
    """

    master_key_path: str    Path to the BD2K Master Key (for S3 Encryption)
    url: str                S3 URL (e.g. https://s3-us-west-2.amazonaws.com/bucket/file.txt)

    Returns: str            32-byte unique key generated for that URL
    """
    with open(master_key_path, 'r') as f:
        master_key = f.read()
    assert len(master_key) == 32, 'Invalid Key! Must be 32 characters. ' \
                                  'Key: {}, Length: {}'.format(master_key, len(master_key))
    new_key = hashlib.sha256(master_key + url).digest()
    assert len(new_key) == 32, 'New key is invalid and is not 32 characters: {}'.format(new_key)
    return new_key
