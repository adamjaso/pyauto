CREATE TABLE IF NOT EXISTS mac_vendor (
  mac_prefix TEXT NOT NULL,
  vendor_name TEXT NOT NULL,
  vendor_address TEXT NOT NULL,
  country CHAR(2) NOT NULL,
  PRIMARY KEY (mac_prefix)
);
