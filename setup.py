from setuptools import setup, find_packages

setup(
    name="django-oscar-es",
    version="0.1",
    packages=find_packages(),
    url="",
    license="MIT",
    author="Joey Jurjens",
    author_email="",
    description="An elasticsearch integration for django-oscar",
    install_requires=[
        "django-oscar",
        "django-elasticsearch-dsl",
    ],
)
