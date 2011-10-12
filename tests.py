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


class MissingValueValuesInDataStructTestCase(unittest.TestCase):
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
        self.assertEqual(m.last_name, lcd.MissingValue)
        
    def test_missing_value_not_serialized(self):
        m = self.model(first_name="john", dob=datetime.date.today())
        self.assertEqual(m.last_name, lcd.MissingValue)
        self.assertFalse("last_name" in m.dump(dumper=lcd.dictdump))


class NestedDataStructureTestCase(unittest.TestCase):
    def setUp(self):
        self.jsondata = """
        {
            "debug": "on",
            "image": [{ 
                "src": "Images/Sun.png",
                "name": "sun1",
                "hOffset": 250,
                "vOffset": 250,
                "alignment": "center"
            },{ 
                "src": "Images/Moon.png",
                "name": "moon",
                "hOffset": 250,
                "vOffset": 250,
                "alignment": "center"
            }],
            "text": {
                "data": "Click Here",
                "size": 36,
                "style": "bold",
                "name": "text1",
                "hOffset": 250,
                "vOffset": 100,
                "alignment": "center",
                "onMouseUp": "sun1.opacity = (sun1.opacity / 100) * 90;"
            }
        }
        """
        class Widget(lcd.DataStruct):
            class Text(lcd.DataStruct):
                data      = lcd.Field()
                size      = lcd.Field()
                style     = lcd.Field()
                name      = lcd.Field()
                hOffset   = lcd.Field()
                vOffset   = lcd.Field()
                alignment = lcd.Field()
                onMouseUp = lcd.Field()
            class Image(lcd.DataStruct):
                src      = lcd.Field()
                name      = lcd.Field()
                hOffset   = lcd.Field()
                vOffset   = lcd.Field()
                alignment = lcd.Field()
            
            text = lcd.StructField(Text)
            image = lcd.StructListField(Image)
            debug = lcd.Field()
        self.model = Widget
        
    def test_load_nested_data(self):
        instance = self.model.load(self.jsondata)
        self.assertTrue(isinstance(instance.image[0], self.model.Image))
        self.assertTrue(isinstance(instance.text, self.model.Text))
        self.assertEqual(len(instance.image), 2)
        self.assertEqual(instance.image[0].name, "sun1")
        self.assertEqual(instance.image[1].name, "moon")
        
            
            


class ClassDumpSchemaModificationTestCase(unittest.TestCase):
    def setUp(self):
        class ModelV1(lcd.DataStruct):
            name = lcd.Field(check=[lcd.verify.not_missing])
            temp = lcd.Field()
        class ModelV2(lcd.DataStruct):
            _ignore_unknown_kws = True
            name = lcd.Field(check=[lcd.verify.not_missing])
        self.model_v1 = ModelV1
        self.model_v2 = ModelV2
        
    def test_missing_field_not_trasnfered(self):
        m1 = self.model_v1(name="john", temp="doe")
        m2 = self.model_v2.load(m1.dump())
        self.assertEqual({"name":"john"},m2.dump(dumper=lcd.dictdump))
        

    
        
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
        
class MissingValueValueTestCase(unittest.TestCase):
    def test_boolean_behavior(self):
        self.assertFalse(lcd.MissingValue)
                



if __name__ == "__main__":
    unittest.main()
