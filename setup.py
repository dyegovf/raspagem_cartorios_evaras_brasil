try:
    from setuptools import setup, find_packages
except ImportError:
    import sys
    print("\n[ERRO] O pacote 'setuptools' não está instalado no Python selecionado.\n"
          "Ative o ambiente virtual correto e instale com: pip install setuptools\n"
          "Ou selecione o Python correto no VS Code (Ctrl+Shift+P > Python: Select Interpreter).\n")
    sys.exit(1)

setup(
    name="cartorios_brasil_scraper",
    version="1.0.0",
    description="Raspagem de dados de cartórios e varas judiciais do Brasil",
    author="Dyego",
    author_email="dyego@[seu-email].com",
    packages=find_packages(include=["scripts", "scripts.*"]),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "pandas>=2.2.2",
        "python-dotenv>=1.0.1"
    ],
    python_requires=">=3.8",
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)