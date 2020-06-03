[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Contributors][contributors-shield]][contributors-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="#">
    <img src="reports/flask-logo.png" alt="Logo" width="256" height="156">
  </a>

  <h3 align="center">Flask API on Scale</h3>

  <p align="center">
    This flask api is tiny part of a whole system implementing data-warehouse.
    <br />
    <br />
    <br />
    <a href="mailto:umairqadir97@gmail.com">Request Demo</a>
    ·
    <a href="https://github.com/umairqadir97/scaling_flask_api/issues">Report Bug</a>
    ·
    <a href="https://github.com/umairqadir97/scaling_flask_api/issues">Request Feature</a>
  </p>
</p>



<!-- TABLE OF CONTENTS -->
## Table of Contents

* [About the Project](#about-the-project)
  * [Built With](#built-with)
* [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
* [Usage](#usage)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)
* [Contact](#contact)



<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot-1]](#about-the-project)

[![Product Name Screen Shot][product-screenshot-2]](#about-the-project)

This POC/ boilerplate API is part of a larger system implementing data-warehousing that was required to normalize data coming from various sources and of different types. The system parsed all the incoming data to common JSON format, before ingestinng to the ware-house. We also parsed PDFs, xmls, html and excel/ csv files along with other databases.


**Why Flask**

Do you think that because Flask is a micro-framework, it must only be good for small, toy-like web applications? Well, not at all! 

Can Flask scale? For many, that is the million dollar question. Unfortunately even the Flask official documentation is ambiguous about this topic. Flask is a small, unobtrusive framework that simplifies the interface between your application and the web server. Outside of that, it mostly stays out of your way, so if you need to write an application that can scale, Flask is not going to prevent it, and in fact, it will allow you to freely choose the components of your stack and not impose choices on you like big frameworks tend to do.


**Key Learnings:**
* Setting up boilerplates for django project
* RESTful API development
* Handling large code base :smile:


[Contributors are always welcomed!](#contributing)

This project still needs some effort to formalize the structure a bit more. And of course, writing the tests.


<br>

### Built With

* [Python](http://python.org/)
* [Flask](https://palletsprojects.com/p/flask/)
* [Pandas](https://pandas.pydata.org/)
* [PDFQuery](https://pypi.org/project/pdfquery/)
* [Tabula-Py](https://pypi.org/project/tabula-py/)



<!-- GETTING STARTED -->
## Getting Started


To get a local copy up and running follow these simple example steps.

### Prerequisites

To run this project,  you should have following dependencies ready:

1. Python3
2. Pip


<br>

### Installation


1. Clone the repo
```sh
git clone https://github.com/umairqadir97/scaling_flask_api.git
```
2. Open terminal in project folder
```sh 
cd scaling_flask_api
```

3. Install python packages
```sh
pip3 install -r requirements.txt
```


6. Run server
```sh
python3 api.py
```

<br>

<!-- USAGE -->
## Usage

Postman collection is provided as part of the solution. 
Visit <a href="https://github.com/umairqadir97/scaling_flask_api/tree/master/postman-collections">Postman Collections</a>

<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/umairqadir97/scaling_flask_api/issues) for a list of proposed features (and known issues).



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b amazing_features`)
3. Commit your Changes (`git commit -m 'Add some Amazing Features'`)
4. Push to the Branch (`git push origin amazing_features`)
5. Open a Pull Request


### Contribution guidelines
1. Writing tests
2. Code review
3. Feature Enhancement

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.



<!-- CONTACT -->
## Contact

Muhammad Umair Qadir - [Email](umairqadir97@gmail.com)

LinkedIn: [LinkedIn](https://linkedin.com/in/umairqadir)


<br>

<!-- ACKNOWLEDGEMENTS -->
## Acknowledgements
* [Flask at scale](https://blog.miguelgrinberg.com/post/flask-at-scale-tutorial-at-pycon-2016-in-portland)
* [Million requests per second](https://www.freecodecamp.org/news/million-requests-per-second-with-python-95c137af319/)




<!-- MARKDOWN LINKS & IMAGES -->

<!-- Contributors -->
[contributors-shield]: https://img.shields.io/github/contributors/othneildrew/Best-README-Template.svg?style=flat-square
[contributors-url]: https://github.com/umairqadir97/learning-management-system/graphs/contributors

<!-- Issues -->
[issues-shield]: https://img.shields.io/github/issues/othneildrew/Best-README-Template.svg?style=flat-square
[issues-url]: https://github.com/umairqadir97/scaling_flask_api/issues

<!-- Lisence -->
[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=flat-square
[license-url]: https://github.com/umairqadir97/learning-management-system/blob/master/LICENSE.txt

<!-- LinkedIn -->
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=flat-square&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/umairqadir

<!-- Product Screenshot -->
[product-screenshot-1]: reports/about-api.png
[product-screenshot-2]: reports/post_api.png
