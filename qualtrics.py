import os, io
from zipfile import ZipFile
import requests
import json
import csv

class Qualtrics:
	class Request:
		def __init__(self, **kwargs):
			self.endpoint = kwargs.get('endpoint')
			self.data_center = kwargs.get('data_center', 'ca1')
			self.url = self.resolve(self.data_center, self.endpoint)
			self.headers = kwargs.get('headers', {})
	
		def resolve(self, data_center, endpoint):
			return 'https://{data_center}.qualtrics.com/API/v3/{endpoint}'.format(
				data_center=data_center,
				endpoint=endpoint
			)
			
		def send(self, method, token, data=None, stream=False):
			headers = self.headers.copy()
			headers.update({'x-api-token': token})
			return requests.request(method, self.url, headers=headers, data=data, stream=stream)

	class Survey:
		def __init__(self, id, name, questions=[]):
			self.id = id
			self.name = name
			self.questions = questions

	class SurveyResponse:
		def __init__(self, **kwargs):
			self.fields = kwargs

		def __str__(self):
			result = ''.join("{0}: {1}".format(k, v) for k, v in self.fields.items())
			return result

	def get_surveys(self, token):
		request = self.Request(endpoint='surveys')
		surveys = []
		while request.url is not None:
			# make request
			response = request.send('get', token)
			body = json.loads(response.text)
			# pull survey names and ids
			for element in body["result"]["elements"]:
				survey = self.Survey(element["id"], element["name"])
				surveys.append(survey)
			# update url for next page
			request.url = body["result"]["nextPage"]
		# sort surveys by name
		surveys.sort(key=lambda x: x.name)
		return surveys
	
	def get_survey_questions(self, token, id):
		request = self.Request(endpoint="surveys/{id}".format(id=id))
		response = request.send('get', token)
		body = json.loads(response.text)
		questions = []
		for question in body["result"]["questions"].values():
			questions.append(question["questionText"])
		return questions
	
	def get_survey_responses(self, token, survey):	
		request = self.Request(
			endpoint='surveys/{id}/export-responses/'.format(id=survey.id),
			headers={'content-type':'application/json'})
		response = request.send('post', token, data='{"format" : "csv", "useLabels": true}')
		body = response.json()
	
		progress = self.Request(
			endpoint=request.endpoint + body['result']['progressId'],
			headers=request.headers)
		status = ''
		while status != 'complete' and status != 'failed':
			response = progress.send('get', token)
			body = response.json()
			status = body['result']['status']
		if status == 'failed':
			raise Exception('failed to download survey: {id}'.format(id=survey.id))
			
		result = []
		response = self.Request(
			endpoint=request.endpoint + body['result']['fileId'] + '/file',
			headers=request.headers
		).send('get', token, stream=True)
		with ZipFile(io.BytesIO(response.content)) as zf:
			with zf.open(survey.name + '.csv') as f:
				text = f.read().decode('utf-8').split('\n')
				for row in csv.reader(text):
					result.append(row)
		return result
