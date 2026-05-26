def main() -> None:
    import typer

    from .cli import cli_main

    typer.run(cli_main)


if __name__ == "__main__":
    main()
