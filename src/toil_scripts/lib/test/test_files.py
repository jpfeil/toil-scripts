import os


def test_mkdirp(tmpdir):
    import os
    from toil_scripts.lib.files import mkdir_p
    dir_path = os.path.join(str(tmpdir), 'test')
    # Exists -- shouldn't throw error
    mkdir_p(str(tmpdir))
    mkdir_p(dir_path)
    assert os.path.isdir(dir_path)


def test_tarball_files(tmpdir):
    from toil_scripts.lib.files import tarball_files
    work_dir = str(tmpdir)
    fpath = os.path.join(work_dir, 'output_file')
    with open(fpath, 'wb') as fout:
        fout.write(os.urandom(1024))
    tarball_files(work_dir=work_dir, tar_name='test.tar', fpaths=[fpath])
    assert os.path.exists(os.path.join(work_dir, 'test.tar'))


def test_move_to_output_dir(tmpdir):
    from toil_scripts.lib.files import move_to_output_dir
    work_dir = str(tmpdir)
    os.mkdir(os.path.join(work_dir, 'test'))
    fpath = os.path.join(work_dir, 'output_file')
    with open(fpath, 'wb') as fout:
        fout.write(os.urandom(1024))
    move_to_output_dir(os.path.join(work_dir, 'test'), [fpath])
    assert os.path.exists(os.path.join(work_dir, 'test', 'output_file'))