import inspect
import os
import glob
import importlib.util


def get_functions():
    result = {}
    paths = glob.glob(os.path.join(os.getcwd(), 'functions', 'functions', '*.py'))
    for path in paths:
        func = importlib.import_module(f'functions.functions.{os.path.basename(path)[:-3]}')
        input_data = [dict(html=data.type_.value, data=dict(name=name, **data.data))
                      for name, data in inspect.getfullargspec(func.Function.__init__).annotations.items()]
        result[func.Function.__id__] = dict(class_=func.Function, input_data=input_data, description=func.Function.__doc__,
                                            function_name=func.Function.__function_name__, id=func.Function.__id__)
    return result


FUNCTIONS = get_functions()
