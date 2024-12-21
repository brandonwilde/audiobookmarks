from argparse import ArgumentParser
from pydantic import BaseModel
from pydantic_core import PydanticUndefined


def generate_arg_parser(model: BaseModel) -> ArgumentParser:
    '''
    Generate an argparse.ArgumentParser from a Pydantic model of the same fields.
    The model config must include a description attribute. This will be used to
    describe the function when the help flag is used.
    '''
    parser = ArgumentParser(description=model.model_config['description'])
    for name, field in model.model_fields.items():
        field_type = field.annotation
        help_text = field.description
        default_value = field.default if field.default is not PydanticUndefined else None

        if field_type == bool:
            parser.add_argument(
                f'--{name}',
                action='store_true',
                help=f'{help_text}' + (f' (default: {default_value})' if default_value is not None else ''),
                )
        else:
            parser.add_argument(
                name,
                type=field_type,
                help=f'{help_text}' + (f' (default: {default_value})' if default_value is not None else ''),
                default=default_value
            )
    return parser