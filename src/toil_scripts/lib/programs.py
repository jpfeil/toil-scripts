import os
import subprocess


def which(program):
    """
    Determines if a program exists

    :param str program: Name of program to check
    :return str: Path to program or None
    """

    def is_exe(f):
        return os.path.isfile(f) and os.access(f, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def docker_call(tool, parameters=None, work_dir='.', env=None, sudo=False, outfile=None):
    """
    Calls Docker, passing along parameters and tool.

    :param str tool: Name of the Docker image to be used (e.g. quay.io/ucsc_cgl/samtools)
    :param list[str] parameters: Parameters to be passed to the tool
    :param str work_dir: Directory to mount into the container via `-v`
    :param dict[str,str] env: Environemnt variables to be added (e.g. dict(JAVA_OPTS='-Xmx15G'))
    :param bool sudo: If True, prepends `sudo` to the docker call
    :param file outfile: Pipe output of Docker call to file handle
    :return int: Exit Code
    """
    base_docker_call = ['docker', 'run',
                        '--log-driver=none',
                        '--rm',
                        '-v', '{}:/data'.format(os.path.abspath(work_dir))]
    if sudo:
        base_docker_call.insert(0, 'sudo')
    if env:
        for e, v in env.iteritems():
            base_docker_call.extend(['-e', '{}={}'.format(e, v)])
    subprocess.check_call(base_docker_call + [tool] + parameters, stdout=outfile)
