db = new Mongo().getDB('kp_checker');

db.createCollection('clients', { capped: false });
db.clients.insert([
  {
    name: '<UNIQUE DISPLAY NAME>',
    login: '<klient.gdansk.uw.gov.pl login>',
    password: '<klient.gdansk.uw.gov.pl password>',
    telegram: 12345678,
    data: '',
  },
]);
