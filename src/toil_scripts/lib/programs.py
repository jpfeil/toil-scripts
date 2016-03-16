import os
import subprocess


def which(program):

    def is_exe(f):
        return os.path.isfile(f) and os.access(f, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def docker_call(tool, parameters=None, work_dir='.', java_opts=None, sudo=False, outfile=None):
    """
    Makes subprocess call of a command to a docker container.


    tool_parameters: list   An array of the parameters to be passed to the tool
    tool: str               Name of the Docker image to be used (e.g. quay.io/ucsc_cgl/samtools)
    java_opts: str          Optional commands to pass to a java jar execution. (e.g. '-Xmx15G')
    outfile: file           Filehandle that stderr will be passed to
    sudo: bool              If the user wants the docker command executed as sudo
    """
    base_docker_call = 'docker run --log-driver=none --rm -v {}:/data'.format(work_dir).split()
    if sudo:
        base_docker_call = ['sudo'] + base_docker_call
    if java_opts:
        base_docker_call = base_docker_call + ['-e', 'JAVA_OPTS={}'.format(java_opts)]
    try:
        if outfile:
            exit_code = subprocess.check_call(base_docker_call + [tool] + parameters, stdout=outfile)
        else:
            exit_code = subprocess.check_call(base_docker_call + [tool] + parameters)
    except subprocess.CalledProcessError:
        raise RuntimeError('docker command returned a non-zero exit status: {}'.format(parameters))
    except OSError:
        raise RuntimeError('docker not found on system. Install on all nodes.')
    return exit_code
