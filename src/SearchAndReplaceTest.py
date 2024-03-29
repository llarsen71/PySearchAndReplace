#This file was originally generated by PyScripter's unitest wizard

import unittest
import SearchAndReplace

class TestReplacer(unittest.TestCase):

  def setUp(self):
    self.r = SearchAndReplace.Replacer()

  def tearDown(self):
    self.r = None

  def testDoReplace(self):
    s = "This is a test"
    self.assertEqual(s, self.r.DoReplace(s))

  def test__call__(self):
    s = "Another Test"
    self.assertEqual(self.r(s),self.r.DoReplace(s))

class TestSimpleReplacer(unittest.TestCase):

  def setUp(self):
    self.r = SearchAndReplace.SimpleReplacer({'Robert':'Bob','I':'me'})

  def tearDown(self):
    self.r = None

  def testAddPair(self):
    self.r.AddPair("William","Bill")
    self.assertEqual("Bob's tales of Bill Tell",self.r("Robert's tales of William Tell"))

  def testDoReplace(self):
    self.assertEqual("Bob and me",self.r("Robert and I"))

class TestRegexReplacer(unittest.TestCase):

  def setUp(self):
    self.r = SearchAndReplace.RegexReplacer({"(b..)":r"_\1_"})

  def tearDown(self):
    self.r = None

  def testAddRegexPair(self):
    pass

  def testDoReplace(self):
    self.assertEqual("_bob_ is a _bot_.",self.r("bob is a bot."))

teststr = \
"""
Robert and I manage the
external website. Robert
does the IT stuff. Bill it.
"""
teststr1 = \
"""
Bob and me manage the
external website. Bob
does the meT stuff. Bill it.
"""
teststr2 = \
"""
ReBob and me manage the
external website. ReBob
does the meT stuff. ReBill it.
"""

class TestSearchAndReplace(unittest.TestCase):

  def setUp(self):
    r = [SearchAndReplace.SimpleReplacer({'Robert':'Bob','I':'me'})]
    self.s = SearchAndReplace.SearchAndReplace(r)

  def tearDown(self):
    self.s = None

  def testAddReplacer(self):
    r = SearchAndReplace.RegexReplacer({"(B..)":r"Re\1"})
    self.s.AddReplacer(r)
    self.assertEqual(teststr2,self.s.DoReplaceStr(teststr))

  def testAddListener(self):
    append_str = "Appended Values.\nNew values at the end.\n"

    def listener(msg,out):
      # Have the listener append a string to the end of the output.
      self.assertEqual(msg,SearchAndReplace.SearchAndReplace.EVT_FINISHED)
      print >>out, append_str,

    self.s.AddListener(listener)
    # Check that the
    self.assertEqual(teststr1+append_str,self.s.DoReplaceStr(teststr))

  def testDoReplace(self):
    import os
    fn = "eraseme.txt"
    f = file(fn,"w")
    f.write(teststr)
    f.close()

    self.s.DoReplace(fn)

    fn2 = fn + ".new"
    self.assertTrue(os.path.exists(fn2),"Search and replace file " + fn2 + " was not created.")
    f = file(fn2)
    result = f.read()
    f.close()
    self.assertEqual(result,teststr1)

    os.remove(fn)
    os.remove(fn2)

  def testDoReplaceStr(self):
    self.assertEqual(teststr1,self.s.DoReplaceStr(teststr))

class TestMatchOverride(unittest.TestCase):

  def setUp(self):
    import re
    pattern = re.compile("(a.)(b.)(c.)")
    def replfunc(mo,index):
      return '_%s_' % mo.other.group(index)
    groupmap = {1:'A(s)',3:replfunc}
    match = pattern.search("a1b2c3")
    self.mo = SearchAndReplace.MatchOverride(match,pattern,groupmap)

  def tearDown(self):
    self.mo = None

  def testgroup(self):
    self.assertEqual('A(s)',self.mo.group(1))
    self.assertEqual('b2',  self.mo.group(2))
    self.assertEqual('_c3_',self.mo.group(3))

  def testexpand(self):
    self.assertEqual('_c3_ b2 A(s)',self.mo.expand(r'\3 \2 \1'))

  def testinsert(self):
    self.assertEqual('_c3_ b2 A(s)', \
          self.mo.insert(r'\3 \2 \1'))

class TestReplacerSwitch(unittest.TestCase):

  def setUp(self):
    SR = SearchAndReplace.SimpleReplacer
    default = SR({'Michael':'Mike'})
    switches = [("switch a",SR({'Robert':'Bob'})),("switch b",SR({'William':'Bill'}))]
    self.switch = SearchAndReplace.ReplacerSwitch(default,switches,False)

  def tearDown(self):
    self.switch = None

  def testAddSwitch(self):
    pass

  def testDoReplace(self):
    line = 'Michael and Robert were with William'
    self.assertEqual(self.switch(line),'Mike and Robert were with William')
    line2 = line + ' switch a'
    self.assertEqual(self.switch(line2),line2)
    self.assertEqual(self.switch(line),'Michael and Bob were with William')
    line2 = line + ' switch b'
    self.assertEqual(self.switch(line2),line2)
    self.assertEqual(self.switch(line),'Michael and Robert were with Bill')
    line2 = line + ' switch a'
    self.assertEqual(self.switch(line2),line2)
    self.assertEqual(self.switch(line),'Michael and Bob were with William')

class TestGlobalFunctions(unittest.TestCase):

  def testcompile(self):
    p = SearchAndReplace.compile("(a.)(b.)",{1:"test"})
    self.assertTrue(isinstance(p,SearchAndReplace.PatternDecorator))

class TestPatternDecorator(unittest.TestCase):

  def setUp(self):
 
    def test(match,index):
      return "test_" + match.group(index,False)

    # This is used to indicate the handler for the values extracted by the regex /1=(a.), /2=(b.), /3=(c.)
    # For the first item (a.), we just return a "1"
    # For the second item (b.), we call the test function with the match and the index number. This will return "test_2"
    gm = {1:"1",2:test}
    self.pattern = SearchAndReplace.PatternDecorator("(a.)(b.)(c.)",gm)

  def tearDown(self):
    self.pattern = None

  def test__extract_groupmap__(self):
    kw = {'groupmap':'test','other':1}
    value = self.pattern.__extract_groupmap__(kw)
    self.assertEqual(value,'test')
    self.assertTrue('groupmap' not in kw)
    self.assertTrue('other' in kw)

  def testfinditer(self):
    iterat = self.pattern.finditer("a4b3c2 middle a3b4c5")
    match = iterat.next()
    
    # In setup, it was indicated that the first group should be replaced by "1"
    self.assertEqual(match.group(1),"1")
    self.assertEqual(match.group(1,False),"a4")
    # The second group calls the 'test' function in 'setUp'
    self.assertEqual(match.group(2),"test_b3")
    self.assertEqual(match.group(2,False),"b3")
    self.assertEqual(match.group(3),"c2")

    match = iterat.next()
    self.assertEqual(match.group(1),"1")
    self.assertEqual(match.group(1,False),"a3")
    self.assertEqual(match.group(2),"test_b4")
    self.assertEqual(match.group(2,False),"b4")
    self.assertEqual(match.group(3),"c5")
    self.assertRaises(StopIteration,iterat.next)

  def testmatch(self):
    match = self.pattern.match("a1b2c3 middle a3b4c5")
    self.assertEqual(match.group(1),"1")
    self.assertEqual(match.group(1,False),"a1")
    self.assertEqual(match.group(2),"test_b2")
    self.assertEqual(match.group(2,False),"b2")
    self.assertEqual(match.group(3),"c3")
    self.assertEqual("1 test_b2 c3",match.expand(r"\1 \2 \3"))
    self.assertTrue(self.pattern.match("not at start a1b2c3") is None)

  def testsubn(self):
    string,n = self.pattern.subn(r"\1 \2 \3","a1b2c3 other stuff a3b4c5")
    self.assertEqual(string,"1 test_b2 c3 other stuff 1 test_b4 c5")
    self.assertEqual(n,2)

    # Test the function returned from subn when no string is passed in.
    fn = self.pattern.subn(r"\1 \2 \3")
    string,n = fn("a1b2c3 other stuff a3b4c5")
    self.assertEqual(string,"1 test_b2 c3 other stuff 1 test_b4 c5")
    self.assertEqual(n,2)

  def testsub(self):
    string,n = self.pattern.subn(r"\1 \2 \3","a1b2c3 one a3b4c5 two")
    self.assertEqual(string,"1 test_b2 c3 one 1 test_b4 c5 two")

    # Test the function returned from sub when no string is passed in.
    fn = self.pattern.subn(r"\1 \2 \3")
    string,n = fn("a1b2c3 one a3b4c5 two")
    self.assertEqual(string,"1 test_b2 c3 one 1 test_b4 c5 two")

  def testsearch(self):
    match = self.pattern.search("one a1b2c3 two a2b3c4")
    self.assertEqual(match.group(1),"1")
    self.assertEqual(match.group(1,False),"a1")
    self.assertEqual(match.group(2),"test_b2")
    self.assertEqual(match.group(2,False),"b2")
    self.assertEqual(match.group(3),"c3")
    self.assertEqual("1 test_b2 c3",match.expand(r"\1 \2 \3"))

    self.assertTrue(self.pattern.search("No Match") is None)

if __name__ == '__main__':
  unittest.main()

