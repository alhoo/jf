import click
from .main import jf


@click.command()
@click.option("--processes", default=1, help="Number of processes to use.")
@click.option(
    "--from_file",
    "-f",
    help="read transformation from file. This is also activated for query strings that ends with '.jf'",
    is_flag=True,
)
@click.option("--import", "imports", help="additional imports.", multiple=True)
@click.option(
    "--import_from",
    "import_path",
    help="additional import path.",
    multiple=True,
    default=[],
)
@click.option("--compact", "-c", help="compact output.", is_flag=True)
@click.option("--debug", help="show debug.", is_flag=True)
@click.option("--init", help="run initialization code", multiple=True)
@click.option("--raw", "-r", help="raw output.", is_flag=True)
@click.option(
    "--input",
    "inputfmt",
    help="force input format (json, yaml, excel, csv, ...)",
    default=None,
)
@click.option(
    "--output",
    "output",
    help="output format (json, yaml, excel, csv, ...)",
    default="json",
)
@click.argument("query_and_files", nargs=-1, default=None)
def main(
    processes,
    query_and_files,
    imports,
    import_path,
    from_file,
    compact,
    inputfmt,
    output,
    debug,
    raw,
    init,
):
    return jf(
        processes,
        query_and_files,
        imports,
        import_path,
        from_file,
        compact,
        inputfmt,
        output,
        debug,
        raw,
        init,
    )


if __name__ == "__main__":  # pragma: no coverage
    main()
