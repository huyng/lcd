import json
import unittest
import lcd
import datetime
class ClassCreationTestCase(unittest.TestCase):

    def setUp(self):
        class Person(lcd.DataStruct):
            first_name = lcd.Field()
            last_name  = lcd.Field()
            dob        = lcd.Field(pre_dump=lambda d: d.strftime("%Y-%m-%d"), post_load=lambda s:datetime.datetime.strptime(s,"%Y-%m-%d"))
        self.model_class = Person
        self.instance    = Person()

    def test_class_created(self):
        """Model instance should be of type DataStruct"""
        self.assertTrue(isinstance(self.instance, self.model_class))

    def test_fields_created(self):
        """Model instance should have a property called _fields"""
        self.assertTrue(hasattr(self.instance, '_fields'))
    
    def test_field_collected(self):
        """Model property should be of correct type"""
        self.assertTrue(isinstance(self.instance._fields['first_name'], lcd.Field))

class ClassCreationFailsTestCase(unittest.TestCase):
    def setUp(self):
        class Person(lcd.DataStruct):
            first_name = lcd.Field(check=[lcd.verify.not_missing])
            last_name  = lcd.Field()
            dob        = lcd.Field(check=[lcd.verify.is_type(datetime.datetime, datetime.date)],
                                   if_missing=datetime.date.today(),
                                   pre_dump=lambda d: d.strftime("%Y-%m-%d"), 
                                   post_load=lambda s:datetime.datetime.strptime(s,"%Y-%m-%d"))
        self.model = Person                           
        
        
        
    def test_fails_because_unexpected_argument(self):
        self.assertRaises(lcd.InvalidDataStructure, self.model, random_arg="john")
        
    def test_fails_because_missing_required_argument(self):
        self.assertRaises(lcd.InvalidDataStructure, self.model, last_name="john")

    def test_fails_because_incorrect_type(self):
        self.assertRaises(lcd.InvalidDataStructure, self.model, first_name="john", last_name="doe", dob="needs date but used a string instead")


class MissingValuesInDataStructTestCase(unittest.TestCase):
    def setUp(self):
        class Person(lcd.DataStruct):
            first_name = lcd.Field(check=[lcd.verify.not_missing])
            last_name  = lcd.Field()
            dob        = lcd.Field(check=[lcd.verify.is_type(datetime.datetime, datetime.date)],
                                   if_missing=datetime.date.today(),
                                   pre_dump=lambda d: d.strftime("%Y-%m-%d"), 
                                   post_load=lambda s:datetime.datetime.strptime(s,"%Y-%m-%d"))
        self.model = Person                           

    def test_missing_value_assigned_when_not_loaded(self):
        m = self.model(first_name="john", dob=datetime.date.today())
        self.assertEqual(m.last_name, lcd.Missing)
        
    def test_missing_value_not_serialized(self):
        m = self.model(first_name="john", dob=datetime.date.today())
        self.assertEqual(m.last_name, lcd.Missing)
        self.assertFalse("last_name" in m.dump(dumper=lcd.dictdump))

        


class ClassDumpSchemaModificationTestCase(unittest.TestCase):
    def setUp(self):
        class ModelV1(lcd.DataStruct):
            name = lcd.Field(check=[lcd.verify.not_missing])
            temp = lcd.Field()
        class ModelV2(lcd.DataStruct):
            name = lcd.Field(check=[lcd.verify.not_missing])
        self.model_v1 = ModelV1
        self.model_v2 = ModelV2
    
    # def test_missing
        
class ClassLoadDumpTestCase(unittest.TestCase):
    def setUp(self):
        class Person(lcd.DataStruct):
            first_name = lcd.Field()
            last_name  = lcd.Field()
            dob        = lcd.Field(check=[lcd.verify.is_type(datetime.datetime, datetime.date)],
                                   pre_dump=lambda d: d.strftime("%Y-%m-%d"), 
                                   post_load=lambda s:datetime.datetime.strptime(s,"%Y-%m-%d"))
        
        self.model_class = Person
        self.instance = Person(first_name="john", last_name="doe", dob=datetime.date(2011,2,1))
        self.dictraw = {
            'first_name': 'john',
            'last_name': 'doe',
            'dob': '2011-02-01'
        }
        self.jsonraw = json.dumps(self.dictraw)

        
    def test_class_loaded(self):
        model = self.model_class.load(self.jsonraw)
        self.assertTrue(isinstance(model, self.model_class))
    
    def test_class_loaded_from_dict(self):
        model = self.model_class.load(self.dictraw, loader=lcd.dictload)
        self.assertTrue(isinstance(model, self.model_class))
    
    def test_dump_class(self):
        jsonraw = self.instance.dump()
        dictraw = self.instance.dump(dumper=lcd.dictdump)
        self.assertEqual(jsonraw, self.jsonraw)
        self.assertEqual(dictraw, self.dictraw)
        
class MissingValueTestCase(unittest.TestCase):
    def test_boolean_behavior(self):
        self.assertFalse(lcd.Missing)
                



if __name__ == "__main__":
    unittest.main()