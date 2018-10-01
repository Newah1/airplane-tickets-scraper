import os
import sys
import requests
import json
import itertools
import threading
import queue as Queue
import random
import time
import csv

#Set the configuration values for this program
from config import *

list_of_search_ids = []
list_of_engine_ids = []
list_search_returns = []
ap_dates = {}
class Downloader(threading.Thread):
	""" Threaded file downloaded """
	current_proxie = ""
	all_proxies = []
	urls = None
	headers = {'Host':'android.momondo.com','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8','Connection':'keep-alive','Accept-Encoding':'gzip, deflate','Accept-Language': 'en-US,en;q=0.8','Content-Type' : 'application/json','User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'}
	def __set_proxy(self,old_proxy = None):
		#set the current proxy to an empty dictionary
		current_proxie = {}
		#Loop at LEAST once.
		while True:
			current_proxie = {"http":random.choice(self.all_proxies)}
			if(old_proxy == None):
				pass
				break
			else:
				if(old_proxy == current_proxie):
					#keep looping
					pass
		#------ end while loop
		return current_proxie
	def __init__(self,queue,proxies):
		threading.Thread.__init__(self)
		self.queue = queue
		self.all_proxies = proxies
	def run(self):
		while True:
			#get the url's from the queue
			url = self.queue.get()
			if ".com" in url:
				print(".com url!")
				self.download(url)
				self.queue.task_done()
			else:
				self.get_urls(url)
				self.queue.task_done()

	def download(self,url,proxy = None):
		global time_to_wait_between_requests
		print("URL!!! "+url)
		headers = self.headers
		contin = True
		this_search = []
		#headers = {'Content-Type' : 'application/json'}
		while contin :
			try:			
				r = requests.get(url,headers=headers,proxies=proxy,timeout=3)
			except Exception as e:
				print(e)
				proxy = self.__set_proxy(proxy)
			else:
				if "403 Forbidden" in r.text:
					time.sleep(time_to_wait_between_requests)
					print(r.text)
					print("403 error, try another IP")

					proxy = self.__set_proxy(proxy)
					print("Proxy new : "+proxy['http'])
					self.download(url,proxy)
				elif r.text == "null":
					print("Null!")
					return True
					pass
				else:
					print("Results loaded successfully, checking if there's more")
					#print("Showing page output:")
					#print(r.text+" r text")
					json_return = r.json()
					this_search.append(json_return)
					if not json_return['Done']:
						print("Not done!")
						
						time.sleep(time_to_wait_between_requests)						
						pass
					else:
						print("Done with search result "+url)						
						global list_search_returns
						list_search_returns.append(this_search)
						return this_search
	pass

	def get_urls(self,json_data,proxy=None):
		global ap_dates
		payload = json_data
		headers = self.headers
		try:
			r = requests.post("http://android.momondo.com/api/3.0/FlightSearch",json=payload,headers=headers,timeout=5,proxies=proxy)
		except Exception as e:
			print(e)
			proxy = self.__set_proxy(proxy)
			self.get_urls(payload,proxy)
		else:
			global time_to_wait_between_requests
			time.sleep(time_to_wait_between_requests)
			if "403 Forbidden" in r.text and not("null" in r.text):
				print(r.text)
				print("403 error, try another IP")

				proxy = self.__set_proxy(proxy)
				print("Proxy new : "+proxy['http'])
				self.get_urls(payload,proxy)
			else:
				json_return = r.json()
				#fe = open("info/search_ids.txt", "w")
				#f.write(str(json_return['SearchId'])+"\r\n")
				#f.close()
				global list_of_search_ids
				global list_of_engine_ids
				search_id = json_return['SearchId']
				ap_dates[search_id] = json_data
				list_of_engine_ids.append(json_return['EngineId'])
				list_of_search_ids.append(json_return['SearchId'])
				print("Got search URL! ID: "+json_return['SearchId'])
				return json_return['SearchId']
	#--------------------------		
			
		pass

#----------
class FlightSearcher():
	files_folder = "files"
	proxies = "proxies.txt"
	
	departs = None
	dests = None
	depart_dates = None
	return_dates = None
	#list of lists filled with departs/returns
	__all_lists = None
	#list filled with proxies
	__proxie_list = None
	#all possible combinations
	__all_combinations = None
	#json search strings
	__json_search_strings = None

	def __init__(self,files_folder,proxies,departs,dests,depart_dates,return_dates = None):
		self.files_folder = files_folder
		self.proxies = proxies
		self.departs = departs
		self.dests = dests
		self.depart_dates = depart_dates
		self.return_dates = return_dates
		self.__proxie_list= self.__create_list(self.proxies)
		print(self.__proxie_list)
		__departs_list = self.__create_list(self.departs)
		__dests_list = self.__create_list(self.dests)
		__depart_dates_list = self.__create_list(self.depart_dates)
		__return_dates_list = self.__create_list(self.return_dates)
		self.__all_lists = [__departs_list,__dests_list,__depart_dates_list,__return_dates_list]
		self.__all_lists = self.__set_empty(self.__all_lists)		
		self.__all_combinations = self.create_combinations(self.__all_lists)
	#--------------------- END __init__()
	def get_combinations(self):
		return self.__all_combinations
	def get_num_combinations(self):
		return len(self.__all_combinations)
	#--------- END
	def get_proxies(self):
		return self.__proxie_list
	def prep_json_search_strings(self):
		pay_return = []
		for combo in combinations:			
			payload = {
			'Culture' : 'en-US',
			'Market' : 'US',
			'Application' : 'Android',
			'Consumer' : 'momondo',
			'Mix' : 'NONE',
			'Mobile' : True,
			'TicketClass' : 'ECO',
			'AdultCount' : 1,
			'ChildAges' : [],
			'Segments' : [
					{
						"Origin" : ""+combo[0],
						"Destination" : ""+combo[1],
						"Departure" : ""+combo[2]
					}
				],
			}
			if not combo[3]:
				pass
			else:
				payload['Segments'].append( {
					"Origin" : combo[1],
					"Destination" : combo[0],
					"Departure" : combo[3]
				})
			#-----------------
			pay_return.append(payload)
		self.__json_search_strings = pay_return
		return pay_return
	def __set_empty(self,all_list):
		for i in range(len(all_list)):
			if not all_list[i]:
				all_list[i] = [None]
				self.__continue_anyway("One or more of the input values were empty. (if return date values, than this may be normal)")
		return all_list
	#-------------------- END __set_empty()
	def __create_list(self,file):
		try:
			f = open(self.files_folder+"/"+file, "r",encoding='utf-8-sig')
		except Exception as e:
			return_list = [None]
			message = ""+file+" is not able to be read."
			self.__continue_anyway(message)
		else:
			lines = f.readline().rstrip()
			return_list = []
			while lines:
				lines.strip()
				return_list.append(lines)
				lines = f.readline().rstrip()
			f.close()
		#-------END TRY
		return return_list
	#-----------END __create_list()
	def create_combinations(self,all_list):
		listed = list(itertools.product(*all_list))
		return listed
	#----------END create_combinations
	def type_to_continue(self,con_string,message = ""):
		print(message+" Type "+con_string+" or enter to continue, or 'exit' to quit.")
		i = input()
		if i == "exit":
			print("Closing program")
			exit()
		else:
			return True
	#---------- END __type_to_continue()
	def __continue_anyway(self,message):
		print("WARNING : "+message+" Press enter to continue anyway, or type exit to close script. (this may cause errors)")
		i = input()
		if i == "exit":
			print("Closing gracefully")
			exit()
		else:
			return True
	#--------- END __continue_anyway()

#------------------END FlightSearcher()

#Create a new FlightSearcher
search = FlightSearcher(files_folder,proxies,departs,dests,depart_dates,return_dates)
# Show number of combinations
if search.type_to_continue("y","There are "+str(search.get_num_combinations())+" possible combinations. "):
	pass
combinations = search.get_combinations()
json_strings = search.prep_json_search_strings()

queue = Queue.Queue()
for i in range(number_of_possible_concurrent_connections):
	t = Downloader(queue,search.get_proxies())
	t.setDaemon(True)
	t.start()
#refer to config.py for information on this
if(limit_results != None):
	json_strings = json_strings[0:limit_results]
else:
	pass
#put the urls into the queue to be processed.
for js in json_strings:
	queue.put(js)
#after every job is finished : 
queue.join()
if search.type_to_continue("y","Done getting search strings! "):
	pass

for i in range(number_of_possible_concurrent_connections):
	t = Downloader(queue,search.get_proxies())
	t.setDaemon(True)
	t.start()
for search_id in list_of_search_ids:
	queue.put("http://android.momondo.com/api/3.0/FlightSearch/"+search_id+"/0")

queue.join()
print("Done with all results!")
#print(list_of_search_ids)
#print(list_search_returns)

#Write the whole result string to a .txt file
f = open("logs/"+str(time.time())+".txt",'w')
f.write(str(json.dumps(list_search_returns)))
f.close()

#Start parsing through the results
offers = []

for i in range(len(list_search_returns)):
	for x in range(len(list_search_returns[i])):
		li = list_search_returns[i][x]
		airport_info = {}
		search_id = ""
		search_id = li['SearchId']
		if(search_id != ""):
			airport_info = ap_dates[search_id]

		if 'Offers' in li and li['Offers'] != None:
			print("Printing out this")
			if('FeeIndexes' in li['Offers']):
				li['Offers'].pop('FeeIndexes',None)			
			offers.extend(li['Offers'])
for i in range(len(offers)):
	offers[i].update(airport_info)

print(offers)
print("Offers 0 ")
print(offers[0].keys())
with open("outputs/"+str(time.time())+".csv","w",newline='') as myfile:
	wr = csv.writer(myfile)
	wr.writerow(offers[0].keys())
	for i in range(len(offers)):
		row = []
		for key, value in offers[i].items():
			row.append(value)
		wr.writerow(row)
#---- end of writing CSV file
input()



def format_proxies(proxies):
	proxy_dict = {}
	for proxy in proxies:
		proxy_dict.update({"http":"http://"+proxy})
	return proxy_dict
#---------------
def get(url):
	"""
	run the program
	"http://android.momondo.com/api/3.0/FlightSearch"
	"""
	proxies = file_to_list("proxies.txt")
	proxies = format_proxies(proxies)	
	payload = {
	'Culture' : 'en-US',
	'Market' : 'US',
	'Application' : 'Android',
	'Consumer' : 'momondo',
	'Mix' : 'NONE',
	'Mobile' : True,
	'TicketClass' : 'ECO',
	'AdultCount' : 1,
	'ChildAges' : [],
	'Segments' : [
			{
				"Origin" : "ATL",
				"Destination" : "GEG",
				"Departure" : "2017-08-22"
			}
		],
	}
	headers = {'Content-Type' : 'application/json','referer' : 'android.momondo.com','User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.4.4)'}
	
	r = requests.post(url,json=payload,headers=headers,timeout=5,proxies=proxies)
	print(r.text)
	response = json.loads(r.text)
	new_url = "http://android.momondo.com/api/3.0/FlightSearch/"+response['SearchId']+"/0"
	print(new_url)
	rn = requests.get(new_url,headers=headers,timeout=60,proxies=proxies)
	print(rn.text)
#---------
def file_to_list(file):
	f = open("files/"+file, "r")
	lines = f.readline()
	return_array = []
	while lines:
		lines.strip()
		print(lines)
		return_array.append(lines)
		lines = f.readline()
	f.close()
	return return_array
#----------
