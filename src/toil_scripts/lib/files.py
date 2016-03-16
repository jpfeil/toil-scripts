import os
import errno
import tarfile
import shutil


def mkdir_p(path):
    """
    It is Easier to Ask for Forgiveness than Permission
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def tarball_files(tar_name, work_dir='.', fpaths=None, uuid=None):
    """
    Tars a group of files together into a tarball

    work_dir: str       Current Working Directory
    tar_name: str       Name of tarball
    uuid: str           UUID to stamp files with
    fpaths: list        list of file paths to include in the tarball
    """
    if fpaths is None:
        fpaths = []
    with tarfile.open(os.path.join(work_dir, tar_name), 'w:gz') as f_out:
        for fpath in fpaths:
            if uuid:
                f_out.add(fpath, arcname=uuid + '.' + os.path.basename(fpath))
            else:
                f_out.add(fpath, arcname=os.path.basename(fpath))


def move_to_output_dir(output_dir, filepaths=None):
    """`
    Moves files from the working directory to the output directory.

    :param output_dir: the output directory
    :param filepaths: list of filepaths
    """
    if filepaths is None:
        filepaths = []
    for fpath in filepaths:
        dest = os.path.join(output_dir, os.path.basename(fpath))
        shutil.move(fpath, dest)
