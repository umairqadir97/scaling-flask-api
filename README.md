# scaling_flask_api
A simple Flask API scaled to Million requests per second


### Prerequisite: 
Python3

### Installation:
$ pip3 install -r requirements.txt
$ python3 api.py


---
##### excel data link: 
https://drive.google.com/drive/u/0/folders/1Enqu8oHsLj0bcyzrg7Gc04mZojxrlMRY
|
|
---
### API Endpoints for Input Data

##### EModel
for i in {1..300}; do wget xdream.eb-cf.com/DR5Bhn9a7.php/EModel/get_list/?page=${i}; done

url: xdream.eb-cf.com/DR5Bhn9a7.php/EModel/get_list/?page=1
method: get
return : {
		code : 1,
		msg: 'success',
		data: [ {'id': 1, 'part_number': 'RC0402FR-0710KL'}]
		}

param description(Parameters in GET method) :
	'page' : default value is 1, each page return 1000 rows;

return value description:
	'code':	the resulting code , if server execute success, the return value is 1 ;
	'msg':	the resulting message;
	'data': the resulting data, if server execute success, the return value is you need
	'id':	model's key ID,
	'part_number':  model's part number


---
##### Ebrand

for i in {1..300}; do wget xdream.eb-cf.com/DR5Bhn9a7.php/Ebrand/get_list/?page=${i}; done

url: xdream.eb-cf.com/DR5Bhn9a7.php/Ebrand/get_list/?page=1
method: get
return : {
		code : 1,
		msg: 'success',
		data: [ {'id': 1, 'part_number': 'RC0402FR-0710KL'}]
		}

param description(Parameters in GET method) :
	'page' : default value is 1, each page return 1000 rows;

return value description:
	'code':		ignore ;
	'msg':		ignore;
	'data':		the resulting data, if server execute success, the return value is you need
	'id':		brand's key ID,
	'brand_name':	brand's name
	'brand_alias':	brand's alias name

---
##### Einbox

url: xdream.eb-cf.com/DR5Bhn9a7.php/Einbox/get_list/?page=1
method: get
return : {
		code : 1,
		msg: 'success',
		data: [ {'id': 1, 'email_date': '2019-12-18 15:48:38'}]
		}

param description(Parameters in GET method) :
	'page' : default value is 1, each page return 100 rows;

return value description:
	'code':		ignore;
	'msg':		ignore;
	'data':		the resulting data, if server execute success, the return value is you need
	'id':		mail's key ID,
	'2019-12-18 15:48:38': mail's datetime 

===================================================================



for i in {1..300}; do wget xdream.eb-cf.com/DR5Bhn9a7.php/Einbox/get/?mid=${i}; done

url: xdream.eb-cf.com/DR5Bhn9a7.php/Einbox/get/?mid=1
method: get
return : {
		code : 1,
		msg: 'success',
		data:  '<html content>'
		}
param description(Parameters in GET method) :
	'mid' : required value, this value must from 'Einbox/get_list';


return value description:
	'code':  ignore;
	'msg': ignore;
	'data': the resulting data, it's a HTML content , and its content had been execute html.escape()

---
