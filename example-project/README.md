# Example use of PyAuto

This example project demonstrates a portable, reproducible automation tool for
downloading the sitemap trees of several websites.

## Using it

Install the requirements. This will set up virtualenv and install required python modules.

```
make install
```

Generate the automation definitions for all the websites.

```
make config
```

Run the automation definition for a single website. You'll have to inspect config.yml and choose a website.
Note that every key in the bottom of the file should be postfixed with `<site_id>_all`.

```
TASK=<site_id>_all make all
```

This will start downloading and extracting the sitemap from robots.txt.
