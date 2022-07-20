import firebase_admin
from firebase_admin import db
import json

txt={"apiKey": "AIzaSyCEf71OQVjBGqnafhVXfiCCGN90YZsdJyo",
  "authDomain": "smart-pepp.firebaseapp.com",
  "projectId": "smart-pepp",
  "storageBucket": "smart-pepp.appspot.com",
  "messagingSenderId": "698016358092",
  "appId": "1:698016358092:web:8a2e5ce49259d08c406c69",
  "measurementId": "${config.measurementId}"}
f={
	"Book1":
	{
		"Title": "The Fellowship of the Ring",
		"Author": "J.R.R. Tolkien",
		"Genre": "Epic fantasy",
		"Price": 100}
}
cred = firebase_admin.credentials.Certificate('C:/Users/jmak1/firebasesdk.json')
default_app = firebase_admin.initialize_app(cred, {
	'databaseURL':"https://smart-pepp-default-rtdb.firebaseio.com/"
	})


##ref = db.reference("/")
##
##file_contents = json.dumps(f)
##ref.set(file_contents)
