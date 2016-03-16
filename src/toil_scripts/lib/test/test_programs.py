def test_which():
    from toil_scripts.lib.programs import which
    assert which('python')


def test_docker_call(tmpdir):
    from toil_scripts.lib.programs import docker_call
    work_dir = str(tmpdir)
    exit_code = docker_call(work_dir=work_dir, parameters=['--help'], tool='quay.io/ucsc_cgl/samtools')
    assert exit_code == 0