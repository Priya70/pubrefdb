## PubRefDB:  Publication database web application.

This web application is an interface to a database of publication
references. It contains bibliographic information and links to relevant
external databases. It allows searching and listing of different subsets
of references, and allows storage and access to related files, such as
supplementary data.

### Login

Login is **not required** from common usage such as searching and listing
of subsets. Administrative actions such as adding new references and
files to the database requires login.

### RESTful interface

The PubRefDb web interface is RESTful, meaning that scripts can easily
be written to access the system from other machines.

### Implementation

The system is written in Python 2.6. The following source code
packages are needed:

- [https://github.com/pekrau/pubrefdb](https://github.com/pekrau/pubrefdb):
  Source code for the **PubRefDb** system.
- [https://github.com/pekrau/wrapid](https://github.com/pekrau/wrapid):
  Package **wrapid** providing the web service framework.
- [https://github.com/pekrau/hypertext](https://github.com/pekrau/hypertext):
  Package **HyperText** for producing the HTML of the web service interface.
- [https://github.com/pekrau/whoyou](https://github.com/pekrau/whoyou):
  Package **WhoYou** providing basic authentication services.
  This can in principle be exchanged for another system.

The [CouchDB database system](http://couchdb.apache.org/) (version 1.0.1
or later) is used as storage back-end in the current implementation.

An example installation can be viewed at
[http://publications.scilifelab.se/](http://publications.scilifelab.se/).
