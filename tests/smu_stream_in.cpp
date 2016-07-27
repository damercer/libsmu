// Simple test for writing data.

#include <csignal>
#include <array>
#include <chrono>
#include <deque>
#include <iostream>
#include <vector>
#include <system_error>
#include <thread>

#include <libsmu/libsmu.hpp>

using std::cout;
using std::cerr;
using std::endl;

using namespace smu;

void signalHandler(int signum)
{
	cerr << endl << "sleeping for a bit to cause an overflow exception" << endl;
	std::this_thread::sleep_for(std::chrono::milliseconds(250));
}

int main(int argc, char **argv)
{
	// Make SIGQUIT force sample drops.
	signal(SIGQUIT, signalHandler);

	// Create session object and add all compatible devices them to the
	// session. Note that this currently doesn't handle returned errors.
	Session* session = new Session();
	session->add_all();

	if (session->m_devices.size() == 0) {
		cerr << "Plug in a device." << endl;
		exit(1);
	}

	// Grab the first device from the session.
	auto dev = *(session->m_devices.begin());

	// Run session at the default device rate.
	session->configure(dev->get_default_rate());

	// Run session in continuous mode.
	session->start(0);

	std::vector<std::array<float, 4>> rxbuf;
	std::deque<float> a_txbuf;
	std::deque<float> b_txbuf;

	// refill Tx buffers with data
	std::function<void(std::deque<float>& buf, unsigned size)> refill_data;
	refill_data = [=](std::deque<float>& buf, unsigned size) {
		for (auto i = buf.size(); i < size; i++) {
			buf.push_back(3);
		}
	};

	while (true) {
		refill_data(a_txbuf, 1024);
		refill_data(b_txbuf, 1024);
		try {
			dev->write(a_txbuf, 0);
			dev->write(b_txbuf, 1);
			dev->read(rxbuf, 1024);
		} catch (const std::system_error& e) {
			// Exit on dropped samples.
			cerr << "sample(s) dropped!" << endl;
			exit(1);
		}

		for (auto i: rxbuf) {
			printf("%f %f %f %f\n", i[0], i[1], i[2], i[3]);
		}
	};
}