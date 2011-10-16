"""
lcd - load, check, dump

verified, declarative, data structures for busy people

"""

class MissingValue:
    """
    The value assigned to fields if they are not loaded 
    from the raw serialized datastructures. If a field
    is set to MissingValue, it will not be serialized through
    the dump function.
    """
    def __nonzero__(self):
        "Mimic the boolean behavior of NoneType"
        return False
    def __str__(self):
        return "lcd.MissingValue"
    def __repr__(self):
        return "lcd.MissingValue"
MissingValue = MissingValue()

class Field(object):
    """
    A generic field that accepts anything and returns everything, 
    as it is, unchanged. Instantiate or inherit from this class
    to customize the field for your data serialization and 
    deserialization needs
    
    Use this by declaring it as a class attribute in a subclass
    of :py:class:`lcd.DataStruct`
    
    :type check:     list or None
    :arg check:      a list of functions of the form f(v)
                     that returns (True, None) if v is valid and
                     returns (False, Reason) if v is invalid.
                     Where Reason is a string explaining why invalidation
                     occured.

    :arg if_missing: a value to assign to the attribute if the attribute
                     is not provided during the model's instantiation
                     (default: lcd.MissingValue).
    
    :arg pre_dump:   a function of the form f(v) that transforms v into
                     a value appropriate for serialization through the
                     :py:func:`lcd.DataStruct.dump` function.

    :arg post_load:  a function of the form f(v) used to transforms v, which is the
                     return value of :py:func:`lcd.DataStruct.load`, into a type 
                     appropriate for use within your app.
    """
    def __init__(self, check=None, if_missing=MissingValue,  pre_dump=None, post_load=None):
        self.validators = [] if not check else check
        self.if_missing = if_missing
        if pre_dump:
            self.pre_dump = pre_dump
        if post_load:
            self.post_load = post_load

    def is_valid(self, appvalue):
        """Checks if value for given field is valid"""
        checks = [validate(appvalue) for validate in self.validators]
        if all(valid for valid, reason in checks):
            return (True, ())
        return (False, [reason for valid, reason in checks if not valid])

    def pre_dump(self, appvalue):
        """
        Called with app data right before performing dump serialization. You can 
        override this during field instantiation or through subclassing.
        """
        return appvalue

    def post_load(self, rawvalue):
        """
        Called with raw data right after performing load deserialization. You can 
        override this during field instantiation or through subclassing.
        """
        return rawvalue

    def __repr__(self):
        return self.__class__.__name__

class StructField(Field):
    """
    A subclass of :py:class:`lcd.Field` that represents a DataStruct within a DataStruct
    
    :arg datastruct: The :py:class:`lcd.DataStruct` subclass to associate with this field
    
    :type check:     list or None
    :arg check:      The list of checks to perform on the datastructure. When these functions
                     run, they will be passed the actual python :py:class:`lcd.DataStruct` instance associated
                     with this field, not the serialized string or raw dictionary.
                     
    :arg if_missing: A value to assign this field if it is missing during load time 
                     or class instantionation
                     
    """
    def __init__(self, datastruct, check=None, if_missing=MissingValue):
        Field.__init__(self,check=check, if_missing=if_missing, pre_dump=struct_dictdump(datastruct), post_load=struct_dictload(datastruct))
        
class StructListField(Field):
    """
    A subclass of :py:class:`lcd.Field` that represents a list of DataStructs within a DataStruct
    
    :arg datastruct: The :py:class:`lcd.DataStruct` subclass to associate with this field
    
    :type check:     list or None
    :arg check:      The list of checks to perform on the datastructure. When these functions
                     run, they will be passed the actual python :py:class:`lcd.DataStruct` instance associated
                     with this field, not the serialized string or raw dictionary.
                     
    :arg if_missing: A value to assign this field if it is missing during load time 
                     or class instantionation
                     
    """
    
    def __init__(self, datastruct, check=None, if_missing=MissingValue):
        Field.__init__(self,check=check, if_missing=if_missing, pre_dump=list_of_structs_dictdump(datastruct), post_load=list_of_structs_dictload(datastruct))


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
        if fields:
            docs = attrs.get('__doc__', '') + "Keyword Arguments:\n\n" \
                + "\n".join([fmt % (k, v) for k,v in fields.items()])
            attrs['__doc__'] = docs
        attrs["_fields"] = fields
        
        return type.__new__(cls, name, bases, attrs)
        
    
class DataStruct(object):
    """
    The base class to be inherited by all objects
    requiring lcd's automatic data validation, serialization,
    and deserilization features.
    
    :arg \*\*kwargs: The values used to instantiate a single DataStruct class.
                     This is automatically generated from any attribute declared 
                     within this class that is an instance of :py:class:`lcd.Field`.
    
    """
    __metaclass__ = DataStructMeta
    
    # set this to true if you want to ignore unknown kws when initializating
    _ignore_unknown_kws = False
    
    def __init__(self, **kwargs):
        """Instantiates and validates datastructure using kwargs defined above"""
        # find kwargs that don't exist in fields
        unknown_kws = set(kwargs).difference(self._fields)
        if not self._ignore_unknown_kws and len(unknown_kws) > 0:
            raise InvalidDataStructure({"error": "%s.__init__ got unexpected keyword arguments: %s" % (self.__class__.__name__,list(unknown_kws)), 
                                        "input kwargs":kwargs})
        
        errors = {}
        for field_name, field in self._fields.items():
            kwarg_value    = kwargs.get(field_name, field.if_missing)
            valid, reasons = field.is_valid(kwarg_value)
            if valid:
                setattr(self, field_name, kwarg_value)
            else:
                errors[field_name] = reasons
        if errors:
            raise InvalidDataStructure({"errors":errors, "input kwargs":kwargs})
                
    @classmethod
    def load(cls, raw, loader=None):
        """
        Loads raw json data and instantiates class using cls(\*\*kwargs). 
        override this as needed
        
        :arg loader: A deserialization function that takes in a string and returns
                     a dictionary representing the data structure to use 
                     (default: json.loads)
        
        """
        loader = loader if loader else json_loads
        kwargs = loader(raw)
        for field_name, field in cls._fields.items():
            if field_name in kwargs:
                kwargs[field_name] = field.post_load(kwargs[field_name])
        # re-raise exception closer to cause
        try:
            instance = cls(**kwargs)
        except InvalidDataStructure, e:
            raise e
        return instance

    
    def dump(self, dumper=None):
        """
        Serializes the DataStruct into your desired serialization
        format. The default serialization format is json
        
        :arg dumper: A serialization function that takes in a 
                     (default: json.dumps)
        """
        to_dump = {}
        dumper = dumper if dumper else json_dumps
        for field_name, field in self._fields.items():
            field_value = getattr(self, field_name)
            if field_value == MissingValue:
                continue
            to_dump[field_name] = field.pre_dump(field_value)
        return dumper(to_dump)


class InvalidDataStructure(TypeError):
    """The exception raised when a data structure is invalid"""
    def __init__(self, errors):
        self.errors = errors
    def __str__(self):
        import pprint
        return "\n\n%s"%pprint.pformat(self.errors)


class verify:
    """A suite of pre-defined check functions"""
    
    @staticmethod
    def is_type(*types):
        """Ensures that the value is one of the specified \*types"""
        def validate(appvalue):
            valid = isinstance(appvalue,types)
            reason = None if valid else "value must be one of these types: %s, recieved %s instead" % ([t.__name__ for t in types], type(appvalue).__name__)
            return (valid, reason)
        return validate
         
    @staticmethod
    def not_missing(appvalue):
        """Ensures that the value is present during load time or instantiation"""
        valid = appvalue != MissingValue
        reason = None if valid else "value is missing"
        return (valid, reason)
    
    @staticmethod
    def one_of(*choices):
        """Ensures that the value is equal to one of the specified \*choices"""
        def validate(appvalue):
            valid = appvalue in choices
            reason = None if valid else "value must be one of the following:%s" % choices
            return (valid, reason)
        return validate

# Utility functions created more for their semantic
# value rather than functionality:

def passthru(value):                    
    """A utility function that returns the same value that it is given. Useful 
    as a loader/dumper to get the dict rather than the serialzied string"""
    return value

def dictload(value):
    """A function that can be used as a loader of dictionary data rather than json data"""
    assert isinstance(value,dict)
    return passthru(value)
    
def dictdump(value):
    assert isinstance(value,dict)
    return passthru(value)

def struct_dictload(datastruct):
    def loader(value):
        return datastruct.load(value, loader=dictload)
    return loader

def struct_dictdump(datastruct):
    def dumper(value):
        return value.dump(dumper=dictdump)
    return dumper

def list_of_structs_dictload(datastruct):
    def loader(value):
        return [datastruct.load(item, loader=dictload) for item in value]
    return loader

def list_of_structs_dictdump(datastruct):
    def dumper(value):
        return [item.dump(dumper=dictdump) for item in value]
    return dumper



# JSON Serialization and Deserialization 
# use cjson if available, otherwise use json
def json_loads(s):
    try:
        from  cjson import decode
        fn = decode
    except ImportError:
        from  json import loads 
        fn = loads
    return fn(s)

def json_dumps(s):
    try:
        from  cjson import encode
        fn = encode
    except ImportError:
        from  json import dumps
        fn = dumps
    return fn(s)