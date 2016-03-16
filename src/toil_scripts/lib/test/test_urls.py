import os
from toil.job import Job


def test_download_from_url(tmpdir):
    from toil_scripts.lib.urls import download_from_url_job
    options = Job.Runner.getDefaultOptions(os.path.join(str(tmpdir), 'test_store'))
    j = Job.wrapJobFn(download_from_url_job, 'www.google.com')
    assert Job.Runner.startToil(j, options)


def test_download_from_url_job(tmpdir):
    from toil_scripts.lib.urls import download_from_url
    work_dir = str(tmpdir)
    download_from_url(work_dir=work_dir, url='www.google.com', name='testy')
    assert os.path.exists(os.path.join(work_dir, 'testy'))


def test_download_from_s3_url(tmpdir):
    from toil_scripts.lib.urls import download_from_s3_url
    work_dir = str(tmpdir)
    fpath = os.path.join(work_dir, 'test')
    url = 's3://cgl-driver-projects/test/rna-test/test.tar.gz'
    download_from_s3_url(fpath, url)
    assert os.path.exists(fpath)


# FIXME -- Need to create dummy encryption key and upload file for testing: Issue #
def test_download_encrypted_file_job(tmpdir):
    from toil_scripts.lib.urls import download_encrypted_file_job
    options= Job.Runner.getDefaultOptions(os.path.join(str(tmpdir), 'test_store'))
    pass


# FIXME -- Requires boto credentials / s3am installed
def test_s3am_upload(tmpdir):
    pass