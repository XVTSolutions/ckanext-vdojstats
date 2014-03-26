

#requirement
pip install reportlab
pip install xhtml2pdf


##tweak for xhtml2pdf with reportlab 3.0
#1: open file /usr/lib/ckan/default/local/lib/python2.7/site-packages/xhtml2pdf/util.py", line 39, in <module>

#2: comment out the below

#if not (reportlab.Version[0] == "2" and reportlab.Version[2] >= "1"):
#REPORTLAB22 = (reportlab.Version[0] == "2" and reportlab.Version[2] >= "2")

#3: add the below
if not (reportlab.Version[:3]>="2.1"):
    raise ImportError("Reportlab Version 2.1+ is needed!")
REPORTLAB22 = (reportlab.Version[:3]>="2.1")


