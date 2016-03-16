import os
import subprocess
from toil.job import Job


def test_download_url_job(tmpdir):
    from toil_scripts.lib.urls import download_url_job
    options = Job.Runner.getDefaultOptions(os.path.join(str(tmpdir), 'test_store'))
    j = Job.wrapJobFn(download_url_job, 'www.google.com')
    Job.Runner.startToil(j, options)


def test_download_url(tmpdir):
    from toil_scripts.lib.urls import download_url
    work_dir = str(tmpdir)
    download_url(work_dir=work_dir, url='www.google.com', name='testy')
    assert os.path.exists(os.path.join(work_dir, 'testy'))


def test_upload_and_download_with_encryption(tmpdir):
    from toil_scripts.lib.urls import s3am_upload
    from toil_scripts.lib.urls import download_url
    from boto.s3.connection import S3Connection, Bucket, Key
    work_dir = str(tmpdir)
    # Create temporary encryption key
    key_path = os.path.join(work_dir, 'foo.key')
    subprocess.check_call(['dd', 'if=/dev/urandom', 'bs=1', 'count=32',
                           'of={}'.format(key_path)])
    # Create test file
    fpath = os.path.join(work_dir, 'output_file')
    with open(fpath, 'wb') as fout:
        fout.write(os.urandom(1024))
    # Upload file
    s3_dir = 's3://cgl-driver-projects/test'
    s3am_upload(fpath=fpath, s3_dir=s3_dir, s3_encryption_key_path=key_path)
    os.remove(fpath)
    # Download the file
    url = 'https://s3-us-west-2.amazonaws.com/cgl-driver-projects/test/output_file'
    download_url(url=url, work_dir=work_dir, s3_encryption_key_path=key_path)
    assert os.path.exists(os.path.join(work_dir, 'output_file'))
    # Delete the Key
    conn = S3Connection()
    b = Bucket(conn, 'cgl-driver-projects')
    k = Key(b)
    k.key = 'test/output_file'
    k.delete()
