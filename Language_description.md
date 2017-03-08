The Language of PerceptionMD
----------------------------

The main goal is to create an easily extendible framework
for phsycophysical experiments in medical environment such
as pairwise comparison between CT volumes or visual grading
analysis, among others.

An experiment is described in a small domain specific language,
and the framework interprets this language.
The language was designed based on markdown notation
to emphasize the human readability and in many parts
it utilizes markdown as a content format.
There must be a non-linebraking whitespace between every two syntactical unit.

## Structure

The language has three main parts:
- <General> for general settings
- <Timeline> for describing the tasks and their relations
- <Content> for including external content, e.g. longer texts.

Every part has its own format.
<General> may contain zero or more key-value pairs (see later).
<Timeline> must contain at least one event and may contain several ones (see later).
<Content> may contain zero or more 'content' (see later).

Key-value pairs:
The key must be a single word where alphanumeric characters,
underscores and dashes are allowed. The key must be followed by equal sign (=),
then by the value the value. Briefly: KEY WHITESPACE = WHITESPACE VALUE, e.g. a = 3.
The values could be integers, floating point numbers, strings or links where
the string must start and end with  quotation marks,  e.g. str = "example string".
Link is a special string encapsulated in a pair of brackerts instead of quotation marks, e.g. [info.txt],
and the string refers to a file or directory. The reference is logical only. Files can be
added at the end of the script in the content section. If there is an entry
in the content section, then the program will not look for the file in the filesystem.
List of values are allowed, they must be comma separated, and one variable
can contain only one type of values.
E.g. valied expression: a = "1","2" invalid expression: b = 1,"2"
Every key-value pair must be a single line expression, linebreaks are not allowed.

Events:
Event is a multiline block.
The first line must start with a dash, then it followed by the type of the event,
then a colon (:), and finally a string which gives the name of the event/task.
This name must be unique, two event are not allowed to have the same name.
The second and following lines in the event description must be indented with at least
two spaces. Every event can have key-value pairs. If these key-values share a key
with the general settings, then this local key-value will be used instead of the global settings.
After the event, the general settings are restored. This is useful when
for instance a default parameter must be changed only for a single task.
The rest of the parameters possibilities depend on the actual event.

'INFO': One of the most simple events is the Info event. This displays a markdown
document in reStructuredText format and waits for a button to press.
The 'text' key is mandatory, the 'button' is optional (it has a default
value: "Next"). For instance:

"""
- INFO: "explanation"
  text = [explanation.md]
  button = "Finish"
"""

'CHOICE' is very similar to a simple 'INFO' event, except that there
are several answer options, and there might be a conditional jump based
on the response. The options are enumerated in the 'options' variable
as strings. The log file will contain both the text of the button and its
number (starting with 0 at the left side).
Conditions may given in 'IF' OPTION_STRING 'THEN' EVENT_NAME format.
There is a strict order: key-values must come first, and conditions
may follow key-values. Mixed order is not allowed.

"""
- CHOICE: "color_blind"
  text = [are_you_color_blind.md]
  options = "Yes", "No", "Don't know"
  IF "Don't know" THEN "test_color_vision"
  IF "Yes" THEN "thanks_but"
"""

'QUESTION' is also meant for data input but instead of selection,
it can ask for open questions, like entering texts and numbers
such as username and age.
First key-value pairs can be given, and 'text' is mandatory.
After the key-value pairs, 'input fields' can be specified
in the following form:
VARIABLE_NAME <- TYPE : DISPLAY_STRING.
The string will be displayed on the left side, and an input field
on the right side. The type can be INT, STRING or FLOAT.
Quotation marks are not allowed in the input, they will be replaced to
a single ' sign.
There is a 'Next' button on the bottom of the screen, and its label
can be overwritten just like in INFO.

"""
- QUESTION: "login"
  text = [login.md]
  button = "Finish"
  username   <- STRING : "Name"
  age        <- INT    : "Age"
  profession <- STRING : "Profession"
  experience <- FLOAT  : "Years of experience"
  comment    <- FLOAT  : "Comment/remark:"
"""

'PAIR' is the event type for pairwise CT volume comparison.
Similarly to previous options, 'text' contain a desciption about the task,
typically a research question, e.g. 'Which image is sharper?'
There might be many options, e.g. forced-choice, choice with tie,
choice with level of confidence, etc.

The volumes are selected from a directory which is given a link (see the example).
Every possible pair in this directory will be asked in a randomized order.
Several directories can be given as a list. In this case, the volumes in
a single link will be paired but volumes from different links will not be.
E.g. dir1 contains 1,2,3, and dir2 contains 4 and 5.
Then the pairs will be: 1-2, 2-3, 1-3, and 4-5.

A single directory link can be repeated. It means that the same pairing will be
asked twice, e.g. 1-2, 2-3, 1-3, 4-5 and 4-5.
The order of the pairs will be randomized before presentation,
and also the volumes can be show up on the left and right side randomly
with uniform probability.

"""
- PAIR: "question1"
    question = [criterion1.md]
    random_pairs = [dcm1], [dcm2], [dcm2], [../another_dcm]
    options = "Left", "Right"

- PAIR: "question2"
    question = [criterion1.md]
    random_pairs = [dcm1],[dcm1]
    options = "Left: Definitely better", "Left: maybe better", "Tie", "Right: maybe better", "Right: Definitely better"
"""

'VGA' is for visual grading analysis. A single CT volume is presented,
and multiple selection questions are asked.
The order of the options will affect the displaying order.
For instance, every question can have its explanation field,
but if it is not necessary, it can be omitted (commented out in the example).

- VGA: "vga1"
    question1 = [criterion1.md]
    options1 = "1","2","3","4"
    explanation1 = [exp1.md]
    question2 = [criterion2.md]
    options2 = "1","2","3"
//    explanation1 = [exp2.md]
    question3 = [criterion3.md]
    options3 = "1","2","3","4"
    explanation3 = [exp3.md]


There are two special events: 'End' and 'Goto'.
None of them has any option, except their name.
'END' terminates the program. An 'END' event is implicitly assumed
after the last event. Explicit declaration of 'END' event is only
needed when the processing flow must be terminated for other reasons.
E.g. It is important to have this option for conditional executions,
for instance, when a user do not agree to accept the terms and conditions,
then the experiment must be ended sooner. Also this event is useful for
debugging purposes.

'GOTO' is an unconditional jump. It might be required to return
to a specific task after some detour. For instance, if the
participant states that he/she is uncertain if he/she has color vision
deficiency, then an additional vision test might be inserted into the
series of tasks. But after this test, the researcher might want to
continue on the same path as people with known condition.
'Goto' is also special because the name label does not give name to this
task. It refers to the task where the execution should be continued.
Therefore, this name must exist as a name for exactly one other event.

"""
- INFO: "explanation"
  text = [explanation.md]
  button = "Finish"
- GOTO: "termination"
- END: "termination"
"""


<Content> part can store link content.
While separation of the documents into different files might improve
the structure, sometimes single file format is preferred.
The storage format is the following:
Content: LINK { CONTENT_TEXT }

CONTENT_TEXT can be multiline text in reStructuredText format,
but it cannot contain these characters: { and }.
The text can contain links, image references, etc., and they will
be rendered on screen, but there is no way to include these referenced
files as 'content', they must be stored as files in the filesystem or
as an entity on the internet.

"""
<Content>

Content: [thanksbut.md] {
Thank you for your time, but unfortunatelly,
if you do not accept the terms and conditions,
then you can't participate in the study.

.. image:: smiley.png
   :aligned: left

Have a nice day.
}
"""

