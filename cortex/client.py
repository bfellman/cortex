import click


def upload_sample(host, port, path):
    """upload sample to server"""
    print(f"yo, {host=}, {port=}, {path=}")


@click.group()
def main():
    pass


@main.command('upload-sample')
@click.option('-h', '--host', default="127.0.0.1", help='target host')
@click.option('-p', '--port', default="8000", help='target port')
@click.argument('path', type=click.File('rb'))
def run_upload_sample(host, port, path):
    upload_sample(host, port, path)


if __name__ == "__main__":
    main()
