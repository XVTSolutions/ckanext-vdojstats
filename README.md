<h1>Requirement</h1>

<h2>installment of the pdf liburaries</h2>
<p>pip install -r pip-requirements.txt
</p>

<h2>tweaking for xhtml2pdf with reportlab 3.0</h2>

<ol>
<li>open file /usr/lib/ckan/default/local/lib/python2.7/site-packages/xhtml2pdf/util.py", line 39, in <module></li>
<li>comment out the below: 
<p>if not (reportlab.Version[0] == "2" and reportlab.Version[2] >= "1"):</p>
<p>raise ImportError("Reportlab Version 2.1+ is needed!")</p>
<p>REPORTLAB22 = (reportlab.Version[0] == "2" and reportlab.Version[2] >= "2")
</p>
</li>

<li>add the below:
<p>if not (reportlab.Version[:3]>="2.1"):</p>
<p>raise ImportError("Reportlab Version 2.1+ is needed!")</p>
<p>REPORTLAB22 = (reportlab.Version[:3]>="2.1")</p>
</li>
</ol>

<h1>Configuration</h1>
<p>Add the below anywhere after the declaration of 'ckan.site_id' into your init file, such as development.ini, production.ini</p>
<ul>
<li>#vdojstats</li>
<li>vdojstats.export_dir = /tmp/export/%(ckan.site_id)s/</li>
<li>vdojstats.export_header = Victoria DoJ</li>
</ul>







