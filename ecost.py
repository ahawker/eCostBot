import time, sys, re
from threading import Thread, Event
from mechanize import Browser, LinkNotFoundError

base_url = 'http://www.ecost.com/'
countdown_url = '%sCountdown.aspx?size=9999999' % (base_url)
checkout_url = '%sCheckout/eCost/Checkout.aspx' % (base_url)
cart_url = '%sShoppingCart.aspx?action=view' % (base_url)

class BotManager:
	def __init__(self):
		self.event = Event()
		self.bots = []
	
	def add_bots(self, bots):
		for b in bots:
			self.bots.append(b)

	def start(self, time_offset=5):
		for b in self.bots:
			b.go(self.event)
			time.sleep(time_offset)
		for b in self.bots:
			b.join()


class Bot(Thread):
	def __init__(self, usr, pwd, pid, sale_cost, notification_email=None, \
				purchase_item=None, max_iterations=sys.maxint, timeout=30):

		self.login = usr
		self.password = pwd
		self.product_id = pid
		self.sale_cost = sale_cost
		self.notification_email = notification_email
		self.purchase_item = purchase_item
		self.max_iterations = max_iterations
		self.timeout = timeout

		self.browser = Browser()
		Thread.__init__(self)
		print "Initializing eCost Bot with login name: %s." % (self.login)

	def go(self, event):
		self.event = event
		self.start()

	def run(self):
		product_found = self._product_search(self.product_id, self.max_iterations, self.timeout)

		if not product_found:
			return

		add_to_cart = self.browser.follow_link(url_regex=product_found.group(1))
		print "Product has been found and added to your shopping cart."

		try:
			view_cart = self.browser.follow_link(url=cart_url)
		except LinkNotFoundError:
			pass

		print "Navigating to checkout page..."
		checkout = self.browser.open(checkout_url)
		
		print "Attempting to login as: %s." % (self.login)
		self._login()

		if self.notification_email:
			self._send_notification_email(self.notification_email)

		if not self.purchase_item:
			print "You have elected not to automatically purchase the item, \
					you must manually log into your eCost account to complete the transaction."
			return
			
		print "Purchase steps redacted."
		print "end"

	def _send_notification_email(self, notification_email):
		import smtplib
		from email.mime.text import MIMEText
		body = "This is a message from your eCostAutobuyer that an item has \
					been added to the shopping cart of your account."
		msg = MIMEText(body)
		msg['Subject'] = "Notification: An item has been added to your eCost account"
		msg['From'] = 'ecostautobuyer@gmail.com'
		msg['To'] = notification_email

		s = smtplib.SMTP('smtp.gmail.com:587')
		s.starttls()
		s.login('email@email.com', 'password')
		s.sendmail('email@email.com', [notification_email], msg.as_string())
		s.quit()
		print "A notification has been sent to %s" % (notification_email)
		
		
	def _product_search(self, product_id, max_iterations, timeout):
		print "Starting our product search for: %s" % (product_id)
		cart_regex = re.compile('<a.*%s.*\s+.*(\d{7,})\_.*.jpg' % (product_id))

		self.browser.open(countdown_url)

		iteration = 0

		while not self.event.isSet():
			source = self.browser.response().read()
			found_item = cart_regex.search(str(source))

			if iteration > max_iterations:
				break
			
			if not found_item:
				time.sleep(timeout)
				iteration += 1
				self.browser.reload()
				continue

			self.event.set()
			return found_item
		return None

	
	def _login(self):
		self.browser.select_form(name='aspnetForm')
		self.browser['ctl00$uxMainPlaceHolder$uxEmail'] = self.login
		self.browser['ctl00$uxMainPlaceHolder$uxPassword'] = self.password
		self.browser.submit()
		print "%s successfully logged in." % (self.login)



def main():
	bm = BotManager()
	b1 = Bot('username', 'password' 'pid', 'sale_cost', 'notification email address')
	b2 = Bot('username', 'password', 'pid', 'sale_cost', 'notification email address')
	bm.add_bots([b1,b2])
	bm.start()
	

main()




