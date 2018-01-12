import yagmail

def mail(content):
	print('starting mail server')
	yag = yagmail.SMTP('HinaNitta')
	to = 'HinaNitta@gmail.com'
	to2 = 'venkat299@gmail.com'
	to3 = 'dev_venkat@outlook.com'
	subject = content[0]
	body = content[1]

	yag.send(to = [to,to2,to3], subject = subject, contents = body)



if __name__ == '__main__':
	mail()
