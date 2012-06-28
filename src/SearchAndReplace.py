def compile(pattern,groupmap=None):
  """
  Similar to the re.compile. However, methods that return Match
  objects or iterators can be passed a groupmap to override the groups
  that are returned. This also affects substition. The groupmap is a
  dictionary that has integer key values. group indexes associated with
  the keys are overridden. The dictionary values can be a string, or a
  function that takes a MatchObject and an index and returns a string.

  pattern  - The regex pattern
  groupmap - A default groupmap to override group values from the Match
             objects.
  """
  return PatternDecorator(pattern,groupmap)

class PatternDecorator:
  """
  Similar to the re Pattern objects. However, methods that return Match
  objects or iterators can be passed a groupmap to override the groups
  that are returned. This also affects substition. The groupmap is a
  dictionary that has integer key values. group indexes associated with
  the keys are overridden. The dictionary values can be a string, or a
  function that takes a MatchObject and returns a string.
  """

  def __init__(self,pattern, groupmap=None):
    """
    pattern  - A regular expression pattern string, or a pattern object.
    groupmap - A default groupmap to use. This overrides the group values
               that come from a match. See MatchOverride.group.
    """
    if isinstance(pattern,str):
      import re
      self._pattern = re.compile(pattern)
    else:
      self._pattern = pattern
    self.groupmap = groupmap

  def __getattr__(self,name):
    return getattr(self._pattern,name)

  def __extract_groupmap__(self,kwargs):
    """
    Extract the groupmap parameter from kwargs if it is there. Delete it
    from the dictionary, and return the value. If it is not contained in
    the dictionary, return the default groupmap passed to the init function.
    """
    # Default to the object groupmap value
    gm = self.groupmap
    if 'groupmap' in kwargs:
      gm = kwargs['groupmap']
      del kwargs['groupmap']
    return gm

  def finditer(self,string,*args,**kwargs):
    """
    Return a match iterator. If groupmap is passed in as a
    keyword argument, then a MatchOverride object is returned that
    has the groupoverride list.

    groupmap - A dictionary of group override values. The indexes are
               integer indices, and the values is a string or a
               function that takes a MatchOverride object and an integer
               index and returns a string.
    """
    gm = self.__extract_groupmap__(kwargs)
    iter = self._pattern.finditer(string,*args,**kwargs)
    for match in iter:
      yield MatchOverride(match,self,gm)

  def match(self,string,*args,**kwargs):
    """
    Create a MatchDecorator object.

    string   - The string to test for a match.
    groupmap - (Optional keyword) A map to override group.
    """
    gm = self.__extract_groupmap__(kwargs)

    match = self._pattern.match(string,*args,**kwargs)
    if match is None: return None

    return MatchOverride(match,self,gm)

  def subn(self,template,string=None,*args,**kwargs):
    """
    Apply a substitution to a string that is passed in using the substition
    template (based on re.subn). If a string is not passed in, then a
    function is returned that accepts strings and returns a modified string.
    The template that was passed in to subn is used as the template for the
    function.

    template - A re.subn rexes template.
    string   - A string to update.
    count    - The number of replacements to make.
    groupmap - (optional keyword) A map to override the group values of the
               MatchDecorator object. See MatchDecorator.group.

    return an updated string and a number of replaces, or (if string is
    None, a function that takes a string and returns a string and number
    of replacements).
    """
    gm = self.__extract_groupmap__(kwargs)

    if gm is None:
      return self._pattern.sub(template,string,*args,**kwargs)

    if len(args) > 0: count = args[0]
    elif 'count' in kwargs: count = kwargs['count']
    else: count = None

    def _subn(string1):
      matches = []
      for i,match in enumerate(self.finditer(string1,groupmap=gm)):
        if count is not None:
          if i == count: break
        # We are assuming that matches come in an increasing sequential
        # order, so we don't sort the values ourselves.
        matches.append(match)

      # We want the values to be processed from the end of the string to the
      # start so that the indexes given in the matches are valid for
      # do string replacement.
      matches.reverse()
      for m in matches:
        string1 = m.insert(template,string1)
      return (string1,len(matches))

    if string is None:
      return _subn
    else:
      return _subn(string)

  def sub(self,template,string=None,*args,**kwargs):
    """
    Apply a substitution to a string that is passed in using the substition
    template (based on re.subn). If a string is not passed in, then a
    function is returned that accepts strings and returns a modified string.
    The template that was passed in to subn is used as the template for the
    function.

    template - A re.subn rexes template.
    string   - A string to update.
    count    - The number of replacements to make.
    groupmap - (optional keyword) A map to override the group values of the
               MatchDecorator object. See MatchDecorator.group.

    return an updated string, or (if string passed in is None, a function
    is returned that takes a string and returns an updated string).
    """
    if string is None:
      fn = self.subn(template,string,*args,**kwargs)
      def _sub(string1):
        line,n = fn(string1)
        return line
      return _sub
    else:
      line,n = self.subn(template,string,*args,**kwargs)
      return line

  def search(self,string,*args,**kwargs):
    """
    string   - A string to search for the pattern associated with this
               Pattern object.
    groupmap - A groupmap to use when returning the match results. See
               MatchDecorator.group for more details.

    return a MatchObject.
    """
    gm = self.__extract_groupmap__(kwargs)
    match = self._pattern.search(string,*args)
    if match is None: return None
    return MatchOverride(match,self,gm)

class MatchOverride:
  """
  This is used to override the re Match object particularly for returning the
  group values.
  """

  def __init__(self,other,pattern=None,groupmap = None):
    """
    other    - A match object that comes from re.match, re.search, or one of
               the items from re.finditer
    pattern  - A compiled regex pattern use to make the match
    """
    self.other = other
    if groupmap is not None:
      self.groupmap = groupmap
    else:
      self.groupmap = {}
    self.pattern = pattern

  def __getattr__(self,name):
    #print name
    return getattr(self.other,name)

  def group(self,index,override=True):
    """
    Get the different matching groups. Note that the groupmap may override
    indexes.

    index    - An integer indicating a group within the regualr expression
               pattern.
    groupmap - A dictionary of substitutions to be used in place of the
               \1 \2 etc values used in the expand template string. The
               value can be a string, or a function that recieves this
               object and the index number and returns a new string.
    """
    if override and index in self.groupmap:
      val = self.groupmap[index]
      if callable(val): return val(self,index)
      return val
    return self.other.group(index)

  def expand(self,template):
    """
    Expand the matching partion using a re.sub template.
    """
    import re
    if self.pattern is None:
      return self.other.expand(self,tempate)
    return re._expand(self.pattern,self,template)

  def insert(self,template,line=None):
    """
    Expand the match and place it in the string that the match came from.
    The template indicates how the match should be explanded and uses
    re.sub syntax. If no line is passed in, the match.string value is used.
    If a line is passed in, it should be consistent with the original
    line that the regular expression match was applied to.

    If there are multiple matches being applied to a line, the substitutions
    should be made from the end of the line forward, and the modified line
    can be passed in each time.
    """
    s = self.start()
    e = self.end()
    if line is None: line = self.string
    return line[0:s] + self.expand(template) + line[e:]

class Replacer:
  """
  This is the base interface for a Replacer. A Replacer should be able to be
  called as a function that receives the line and writes out a modified line
  of text. If None is passed back, nothing is writen to the output.
  """

  def DoReplace(self,line):
    """
    This is a dummy implementation that just passes back what was passed in.
    """
    return line

  def __call__(self,line):
    """
    Enable a replacer to be called as a function. The function should recieve
    the text line and return a modified text line. If None is returned, nothing
    will be writen to the output.
    """
    return self.DoReplace(line)

class SimpleReplacer(Replacer):
  """
  Simple string value replacement based on key value pairs.
  """

  def __init__(self,pairs=None):
    """
    pairs - A dictionary of replacement values. The value to replace is the key,
            and its value is the new value to use.
    """
    if pairs is not None:
      self.replace = pairs
    else:
      self.replace = {}

  def AddPair(self,val,newval):
    """
    Add a substring to replace and the replacement value.

    val    - A substring to replace
    newval - The replacement value
    """
    self.replace[val] = newval

  def DoReplace(self,line):
    for (val,newval) in self.replace.items():
      line = line.replace(val,newval)
    return line

class RegexReplacer(Replacer):
  """
  This recieves a set of regex replacement / substition pairs and applies the
  pairs to the lines that are passed in.
  """

  def __init__(self,pairs=None):
    """
    pairs - A dictionary of pattern and substitution values. The pattern is the
            key value.
    """
    self.replace = {}
    if pairs is not None:
      for (k,v) in pairs.items():
        self.AddRegexPair(k,v)

  def AddRegexPair(self,pattern,template):
    """
    Add a pattern and substitution string pair.

    pattern  - The regex pattern. This may also be a re.sub function of
               the form:
                  sub(template,line)
               This takes a re.sub template string and a line and returns the
               modified line.
    template - The substitution string associated with the pattern
    """
    import re
    if callable(pattern):
      self.replace[template] = pattern
    else:
      self.replace[template] = re.compile(pattern).sub

  def DoReplace(self,line):
    for (template,sub) in self.replace.items():
      line = sub(template,line)
    return line

class ReplacerSwitch(Replacer):
  """
  A ReplacerSwitch object is used to select an active replacer. Each replacer
  is associated with a switch function which decides whether the replacer should
  be active. Only one replacer is active at a time (based on the first switch to
  be triggered). The replacer remains active until a new switch is triggered. A
  default replacer chan be set in the constructor
  """

  SWITCH   = "SWITCH"
  REPLACER = "REPLACER"

  def __init__(self, default_replacer=None, constructs=None, switch_line_check=True):
    """
    default_replacer  - This is the default replacer to use until a case matches.
                        If none is specified, the string that comes in is
                        returned unmodified.

    constructs        - An array of tuples that are arguments to AddSwitch. The
                        AddSwitch function is called with each of the parameters
                        in the array.

    switch_line_check - Switch Line Check - Use the replacer on the lines that
                        match the switch conditions. Default is True.
    """
    self.switches          = []
    self.default           = default_replacer
    self.current_replacer  = default_replacer
    self.switch_line_check = switch_line_check
    if constructs is not None:
      for params in constructs:
        self.AddSwitch(*params)

  def AddSwitch(self, switch_rule, replacer):
    """
    Add a switch rule and a replacer. The switch rule is used to test lines
    to determine whether the replacer should be used. The replacer with the
    firsst switch that indicates true is used.

    switch_rule - The switch rule is either a regualr expression string to match
                  or a function that returns None to indicate a nonmatch, or a
                  value to indicate a match.

    replacer    - This is a function which recieves a string and returns a
                  modified string.
    """
    import re
    switch = {}
    # Convert a string match pattern into a switch to test
    if isinstance(switch_rule,str) == True:
      switch_rule    = re.compile(switch_rule).search
    switch[self.SWITCH]   = switch_rule
    switch[self.REPLACER] = replacer
    self.switches.append(switch)

  def DoReplace(self,line):
    """
    Modify a line of text. The line is modified by the currently active replacer.

    line - Line that is to be modified
    """
    # First check to see if a switch is satisfied
    for switch in self.switches:
      if switch[self.SWITCH](line) is not None:
        self.current_replacer = switch[self.REPLACER]
        if not self.switch_line_check:
          return line
        break
    return self.current_replacer(line)

class SearchAndReplace:
  """
  This class is used to do search and replace on strings or files. For files,
  it reads the file into memory as a string, applies the replacer operations
  line by line, and writes out the results to another file.
  """

  EVT_FINISHED = "FINISHED"

  def __init__(self, replacers=None):
    self.listeners = []
    if replacers is None:
      self.replacers = []
    else:
      self.replacers = replacers

  def AddReplacer(self,replacer):
    """
    Add a Replacer to the list of replacers. The replacer is a Replacer object
    or a function that takes a line and returns a line.

    replacer - A replacer object
    """
    self.replacers.append(replacer)

  def GetReplacers(self):
    return self.replacers

  def AddListener(self,listener):
    """
    Add an event listener. The event is a string value. Event strings are
    class variables that start with EVT_. The event listener is a function that
    receives a string value and the StringIO object for the file.
    """
    if listener not in self.listeners: self.listeners.append(listener)

  def RemoveListener(self,listener):
    """
    Remove an event listener.
    """
    if listener in self.listeners: self.listeners.remove(listener)

  def DoReplace(self,filename,outfile=None):
    """
    Do search and replace on a file. The Replacers need to be configured before
    this call is made, or nothing will happen.

    filename - Name of the file to apply Search and Replace on.
    outfile  - The file to write out - default is '<filename>.new'
    """
    if filename is None: return

    if outfile is None: outfile = filename+'.new'
    lines = open(filename)
    out   = open(outfile,'w')
    self.__DoReplace__(lines,out)
    lines.close()
    out.close()

  def DoReplaceStr(self,str):
    """
    Do search and replace on a string. The Replacers need to be configured
    before this call is made, or nothing will happen.

    str - The string that Search and Replace is applied to.

    Returns the modified string.
    """
    import StringIO
    out = StringIO.StringIO()

    lines = str.splitlines(True)
    self.__DoReplace__(lines,out)

    result = out.getvalue()
    out.close()
    return result

  def __DoReplace__(self, lines, out):
    """
    lines - an iterator that holds the lines to process.
    out   - a file like stream to write values to.
    """
    for (i,line) in enumerate(lines):
      for DoReplace in self.GetReplacers():
        line = DoReplace(line)
      # Don't write out the line if we get None back.
      if line is not None: print >>out, line,

    for listener in self.listeners:
      listener(self.EVT_FINISHED, out)
