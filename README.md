# Bienvenu à l'outil EnR

Tableau de bord des énergies renouvelables, dans le cadre de la mission connaissance, pôle Grand Est.

## Installation

Python 3.8+ et [pip](https://pip.pypa.io/en/stable/) sont nécessaires.

```shell
git clone https://github.com/blenzi/enr-app.git
pip install -e enr-app/.
```

## Running
```shell
streamlit run enr-app/01_🏠_Accueil.py 
```

Il faut avoir les données sur le répertoire `data/` ou avoir accès au `S3` du [SSPCloud](https://docs.sspcloud.fr/onyxia-guide/stockage-de-donnees): `s3/projet-connaissance-enr`.

## Creation et utilisation de conteneur

### Au SSPcloud

L'application est deployée avec `helm` en utilisant le package [enr-deployment](https://github.com/blenzi/enr-deployment) et est accessible sur [https://enr.lab.sspcloud.fr/](https://enr.lab.sspcloud.fr/).


### En local

```shell
docker build -t blenzi/enr_app .
docker run --rm -p 3838:3838 blenzi/enr_app
```

L'application sera disponible sur [localhost:3838](localhost:3838).
