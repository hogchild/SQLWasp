#!/usr/bin/env python3.12
# custom_errors.py
import sys
from typing import Generator

import click
from rich.console import Console
from rich.markdown import Markdown

from data.input.payloader.payloader_config import sql_payloads_by_attack_type

c = Console()


class Payloader:
    """
    The Payloader class is able to retrieve data from a dict[str, dict[str, list[tuple[str, str]]]]
    data structure, i.e.:
        - <data_source> = {<attack_type>: {<dbms_name>: [(<sql_payload>), (<sql_payload>)]}}
    For example:
        - sql_payloads_by_attack_type = {"Boolean-Based": {"PostgreSQL": [(<sql_payload>), (<sql_payload>)]}}
    Included Attack Types: \n
    * 'Boolean-Based'
    Included DBMSs: \n
    * 'PostgreSQL'
    """

    def __init__(
            self, payloads_by_attack_type: dict[str, dict[str, list[tuple[str, str]]]] = sql_payloads_by_attack_type
    ):
        """
        Instantiates the Payloader class. It sets the data sources
        """
        self.c = Console()
        self.payloads_by_attack_type = payloads_by_attack_type

    def show_attack_types(self) -> list:
        """
        Displays all SQL Injection Attack Types (ie: Time-Based, Boolean-Based, etc.)
        for which payloads are available.
        :return: A list of Attack Types.
        """
        self.c.print(Markdown("# Showing all Attack Types"), "\n")
        attack_types = []
        for attack_type in self.payloads_by_attack_type.keys():
            attack_types.append(attack_type)
        return attack_types

    def show_db_engines(self) -> list:
        """
        Displays all DB Engines (DBMS) for which payloads are available.
        :return: A list of DBMS Names.
        """
        self.c.print(Markdown("# Showing all DBMS Names"), "\n")
        dbms_names = []
        for attack_type, dbms_value in self.payloads_by_attack_type.items():
            if isinstance(dbms_value, dict):
                for dbms_name in dbms_value.keys():
                    dbms_names.append(dbms_name)
                return dbms_names

    def get_payloads(
            self, chosen_attack_type: str = None, chosen_dbms_name: str = None,
    ) -> Generator[tuple[str, str], None, None]:
        """
        This method is responsible for retrieving the payloads from the actual data structure.
        The data structure is a bidimensional dictionary, the most internal containing a list
        of tuples with the payloads (ie: dict[str, dict[str, list[tuple[str, str]]]]).
        :param chosen_attack_type:
        :param chosen_dbms_name:
        :return:
        """
        try:
            if chosen_attack_type and chosen_dbms_name:
                self.c.print(f"All payloads from {chosen_attack_type} attack types for {chosen_dbms_name}. \n")
                yield from [pair for pair in self.payloads_by_attack_type[chosen_attack_type][chosen_dbms_name]]
            elif chosen_attack_type and not chosen_dbms_name:
                self.c.print(f"All payloads from {chosen_attack_type} attack types for all DBMSs. \n")
                for dbms_name in self.payloads_by_attack_type[chosen_attack_type]:
                    yield from [pair for pair in self.payloads_by_attack_type[chosen_attack_type][dbms_name]]
            elif not chosen_attack_type and chosen_dbms_name:
                self.c.print(f"All payloads from all attack types for {chosen_dbms_name}. \n")
                for attack_type in self.payloads_by_attack_type.keys():
                    yield from [pair for pair in self.payloads_by_attack_type[attack_type][chosen_dbms_name]]
            elif not chosen_attack_type and not chosen_dbms_name:
                self.c.print(f"All payloads from all attack types for all DBMSs. \n")
                for attack_type in self.payloads_by_attack_type.keys():
                    for dbms_name in self.payloads_by_attack_type[attack_type].keys():
                        yield from [pair for pair in self.payloads_by_attack_type[attack_type][dbms_name]]
        except KeyError as e:
            self.c.print(Markdown(
                f"**Database Query Details:** \n"
                f"* Chosen Attack Type '{chosen_attack_type or None}'. \n"
                f"* Chosen DataBase Engine (DBMS): '{chosen_dbms_name or None}'. \n\n"
                f"Error: Wrong search value _'{e.args[0]}'_. Please review your query."
            ), "\n"
            )


@click.command(
    help=(
            "This script provides two-string tuples of SQL Injections payloads, selected specifically for "
            "vulnerability discovery. It retrieves data from a bidimensional dictionary, where the payloads "
            "are categorized by 'Attack Type' and 'DBMS Name'."
    )
)
@click.option(
    "-a", "--attack", "--attack-type", "attack_type",
    help=(
            "Specify an attack type you want to carry out, like 'Boolean-Based' or 'Time-Based', etc.\n"
            "See all options with '--show-attack-types'."
    ),
    required=False,
    default=None,
    show_default=True
)
@click.option(
    "-e", "--engine", "--db-engine", "db_engine",
    help=(
            "Specify a DB Engine (DBMS) you you want to test against, like 'PostgreSQL' or 'MySQL', etc.\n"
            "See all options with '--show-db-engines'."
    ),
    required=False,
    default=None,
    show_default=True
)
@click.option(
    "-s", "--show-attacks", "show_attacks",
    help="Show all available attack types. Can be used in conjunction with '--show-db-engines.",
    is_flag=True,
    required=False,
    default=False,
    show_default=True
)
@click.option(
    "-d", "--show-db-engines", "show_db_engines",
    help="Show all available attack types. Can be used in conjunction with '--show-attack-types.",
    is_flag=True,
    required=False,
    default=False,
    show_default=True
)
def main(attack_type, db_engine, show_attacks, show_db_engines):
    payloader = Payloader()

    if not show_attacks and not show_db_engines:
        payload_gen = payloader.get_payloads(
            chosen_attack_type=attack_type,
            chosen_dbms_name=db_engine
        )
        for payload in payload_gen:
            c.print(payload)
    else:
        if show_attacks:
            if attack_type or db_engine:
                c.print("Cannot use '-s' flag with '-e'.")
                sys.exit(1)
            c.print(payloader.show_attack_types())
        if show_db_engines:
            if attack_type or db_engine:
                c.print("Cannot use '-s' flag with '-e'.")
            c.print(payloader.show_db_engines())


if __name__ == '__main__':
    main()
