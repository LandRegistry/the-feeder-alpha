import mock
import json

from worker import PublicTitlesWorker, queue, queue_key

test_message = ('titles_queue',
            '''{'proprietors': [
                    {'first_name': 'Gustavo', 'last_name': 'Fring'}, {'first_name': '', 'last_name': ''}],
            'title_number': 'TN1234567',
            'property': {'address':
                                    {'house_number': '1', 'town': 'Albuquerque', 'postcode': '98765', 'road': 'Somewhere'},
            'class_of_title': 'qualified',
            'tenure': 'freehold'},
            'payment': {'titles': ['1234'],
            'price_paid': '987654321'}}''')


expected_public_data = {'title_number': 'TN1234567', 'house_number': '1',  'town': 'Albuquerque', 'postcode': '98765', 'road': 'Somewhere', 'price_paid': '987654321'}

def test_build_public_data():
    worker = PublicTitlesWorker(queue, queue_key)

    public_data = worker.build_public_data(test_message)

    assert public_data == expected_public_data

@mock.patch("requests.put")
def test_worker_should_put_data_to_destinations(mock_put):
    worker = PublicTitlesWorker(queue, queue_key)

    public_data = worker.build_public_data(test_message)
    headers = {"Content-Type": "application/json"}
    base_destination_url = 'http://public-titles-api/title'
    full_destination_url = '%s/%s' % (base_destination_url,  public_data['title_number'])

    worker.send(base_destination_url, public_data)

    mock_put.assert_called_with(full_destination_url, data=json.dumps(public_data), headers=headers)