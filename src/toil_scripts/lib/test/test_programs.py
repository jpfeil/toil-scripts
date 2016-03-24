import os


def test_which():
    from toil_scripts.lib.programs import which
    assert which('python')


def test_docker_call(tmpdir):
    from toil_scripts.lib.programs import docker_call
    work_dir = str(tmpdir)
    parameter = ['--help']
    tool = 'quay.io/ucsc_cgl/samtools'
    docker_call(work_dir=work_dir, parameters=parameter, tool=tool)
    # Test outfile
    fpath = os.path.join(work_dir, 'test')
    with open(fpath, 'w') as fout:
        docker_call(work_dir=work_dir, parameters=parameter, tool=tool, outfile=fout)
    assert os.path.getsize(fpath) > 0
    # Test env
    cmd = docker_call(work_dir=work_dir, parameters=parameter, tool=tool, env=dict(JAVA_OPTS='-Xmx15G'))
    assert '-e JAVA_OPTS=-Xmx15G' in ' '.join(cmd)