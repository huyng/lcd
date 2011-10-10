"""
lcd - load, check, dump

verified, declarative, data structures for busy people

"""
import json
import operator

class Missing:
    """
    The value assigned to fields if they are not loaded 
    from the raw serialized datastructures. If a field
    is set to Missing, it will not be serialized through
    the dump function.
    """
    def __nonzero__(self):
        "Mimic the boolean behavior of NoneType"
        return False
Missing = Missing()

class Field(object):
    def __init__(self, check=None, if_missing=Missing,  pre_dump=None, post_load=None):
        """Generic field  that accepts anything and returns everything, as it is, unchanged
        
        check      -- a list of functions of the form f(v)
                      that returns (True, None) if v is valid and
                      returns (False, Reason) if v is invalid.
                      Where Reason is a string explaining invalidation

        if_missing -- a value to assign to the attribute if the attribute
                      is not provided during the model's instantiation
                      (default: lcd.Missing).
        
        pre_dump   -- a function of the form f(v) that transforms v into
                      a value appropriate for serialization through the
                      dump function.
        
        post_load  -- a function of the form f(v) that transforms v from
                      a value loaded from serialization into a type appropriate
                      for use within your app.
        """

        self.validators = [] if not check else check
        self.if_missing = if_missing
        if pre_dump:
            self.pre_dump = pre_dump
        if post_load:
            self.post_load = post_load

    def is_valid(self, appvalue):
        "Checks if value for given field is valid"
        checks = [validate(appvalue) for validate in self.validators]
        if all(valid for valid, reason in checks):
            return (True, ())
        return (False, [reason for valid, reason in checks if not valid])

    def pre_dump(self, appvalue):
        "Called with app data right before performing dump serialization"
        return appvalue

    def post_load(self, rawvalue):
        "Called with raw data right after performing load deserialization"
        return rawvalue

    def __repr__(self):
        return self.__class__.__name__
        
    
class DataStructMeta(type):

    def __new__(cls, name, bases, attrs):
        fields = {}
        colwidth = 0
        
        # find and collect all instances of Field
        for key, value in attrs.items():
            if isinstance(value,Field):
                colwidth = max(len(key), colwidth)
                fields[key] = value
                attrs.pop(key)
        
        # modify classe's doc string to add kwargs
        fmt = "\t%%-%ss -- %%s" % colwidth
        docs = attrs.get('__doc__', '') \
               + "Keyword Arguments:\n\n" \
               + "\n".join([fmt % (k, v) for k,v in fields.items()])
        attrs['__doc__'] = docs
        attrs["_fields"] = fields
        
        return type.__new__(cls, name, bases, attrs)
        

    
class DataStruct(object):
    __metaclass__ = DataStructMeta
    
    def __init__(self, **kwargs):
        """Instantiates and validates datastructure using kwargs defined above"""
        # find kwargs that don't exist in fields
        unknown_kws = set(kwargs).difference(self._fields)
        if len(unknown_kws) > 0:
            raise InvalidDataStructure("__init__ got unexpected keyword arguments: %s" % list(unknown_kws))
        
        errors = {}
        for field_name, field in self._fields.items():
            kwarg_value    = kwargs.get(field_name, field.if_missing)
            valid, reasons = field.is_valid(kwarg_value)
            if valid:
                setattr(self, field_name, kwarg_value)
            else:
                errors[field_name] = reasons
        if errors:
            raise InvalidDataStructure(errors)
                
    @classmethod
    def load(cls, raw, loader=json.loads):
        """Loads raw json data and instantiates class using cls(**kwargs). override this as needed
        
        Arguments:
        
        using -- a loader deserialization function to use (default: json.loads)
        
        """
        kwargs = loader(raw)
        for field_name, field in cls._fields.items():
            if field_name in kwargs:
                kwargs[field_name] = field.post_load(kwargs[field_name])
        return cls(**kwargs)
    
    def dump(self, dumper=json.dumps):
        """Creates raw json data from self.__dict__. override this as needed
        
        Arguments:
        
        using -- a dumper serialization function to use (default: json.dumps)
        """
        to_dump = {}
        for field_name, field in self._fields.items():
            field_value = getattr(self, field_name)
            if field_value == Missing:
                continue
            to_dump[field_name] = field.pre_dump(field_value)
        return dumper(to_dump)

class InvalidDataStructure(TypeError):
    def __init__(self, errors):
        self.errors = errors
    def __str__(self):
        import pprint
        return "\n%s"%pprint.pformat(self.errors)


## checks
def comparer_check(op, opsym):
    def validate_builder(right):
        def validate(left):
            valid  = op(left,right)
            reason = None if valid else "%s %s %s is not True " % (left,opsym,right)
            return (valid,reason)
        return validate
    return validate_builder

class validate:
    is_eq  = staticmethod(comparer_check(operator.eq, "=="))
    is_gte = staticmethod(comparer_check(operator.ge, ">="))
    is_gt  = staticmethod(comparer_check(operator.gt, ">"))
    is_lte = staticmethod(comparer_check(operator.le, "<="))
    is_lt  = staticmethod(comparer_check(operator.lt, "<="))
    
    @staticmethod
    def is_type(*types):
        def validate(appvalue):
            valid = isinstance(appvalue,types)
            reason = None if valid else "value must be one of these types: %s, recieved %s instead" % ([t.__name__ for t in types], type(appvalue).__name__)
            return (valid, reason)
        return validate
         
    @staticmethod
    def not_missing(appvalue):
        valid = appvalue != Missing
        reason = None if valid else "value is missing"
        return (valid, reason)
    
    @staticmethod
    def one_of(*choices):
        def validate(appvalue):
            valid = appvalue in choices
            reason = None if valid else "value must be one of the following:%s" % choices
            return (valid, reason)
        return validate

# Functions 
def passthru(value):
    "A utility function that returns the same value that it is given. useful as a loader/dumper"
    return value

def dictload(value):
    assert isinstance(value,dict)
    return passthru(value)
    
def dictdump(value):
    assert isinstance(value,dict)
    return passthru(value)