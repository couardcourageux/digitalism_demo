"""
Extracteur CSV pour lire les fichiers CSV dans le pipeline ETL.

Ce module implémente un extracteur qui lit les fichiers CSV en utilisant
le module standard csv de Python, sans dépendance externe comme pandas.
"""

import csv
from pathlib import Path
from typing import Iterator, Dict, Any, Optional

from src.etl.extractors.base_extractor import BaseExtractor
from src.etl.config import CSV_ENCODING, CSV_DELIMITER, CSV_QUOTECHAR


class CSVReader(BaseExtractor):
    """
    Extracteur pour lire les fichiers CSV.

    Cette classe utilise le module csv standard de Python pour lire
    les fichiers CSV ligne par ligne, ce qui permet de traiter
    des fichiers volumineux sans charger tout en mémoire.

    Attributes:
        file_path: Chemin vers le fichier CSV à lire
        encoding: Encodage du fichier (par défaut: UTF-8)
        delimiter: Délimiteur CSV (par défaut: virgule)
        quotechar: Caractère de citation (par défaut: guillemet)
        logger: Logger pour tracer les opérations
    """

    def __init__(
        self,
        file_path: Path,
        encoding: Optional[str] = None,
        delimiter: Optional[str] = None,
        quotechar: Optional[str] = None,
    ):
        """
        Initialise le lecteur CSV.

        Args:
            file_path: Chemin vers le fichier CSV à lire
            encoding: Encodage du fichier (par défaut: utilise la config)
            delimiter: Délimiteur CSV (par défaut: utilise la config)
            quotechar: Caractère de citation (par défaut: utilise la config)
        """
        super().__init__(component_name="csv_reader", component_type="extractor")
        self.file_path = Path(file_path)
        self.encoding = encoding or CSV_ENCODING
        self.delimiter = delimiter or CSV_DELIMITER
        self.quotechar = quotechar or CSV_QUOTECHAR
        self._file_handle = None

    def read(self) -> Iterator[Dict[str, Any]]:
        """
        Lit le fichier CSV et retourne un itérateur de dictionnaires.

        Cette méthode utilise DictReader du module csv pour lire le fichier
        ligne par ligne. La première ligne est utilisée comme en-tête pour
        les clés des dictionnaires.

        Yields:
            Dictionnaire représentant une ligne du CSV, où les clés sont
            les noms des colonnes et les valeurs sont les données de la ligne.

        Raises:
            FileNotFoundError: Si le fichier CSV n'existe pas
            IOError: Si une erreur de lecture survient
            csv.Error: Si le format CSV est invalide
        """
        if not self.file_path.exists():
            self.logger.error(f"Fichier CSV introuvable: {self.file_path}")
            raise FileNotFoundError(f"Le fichier CSV n'existe pas: {self.file_path}")

        self.logger.info(f"Ouverture du fichier CSV: {self.file_path}")

        try:
            with open(self.file_path, "r", encoding=self.encoding, newline="") as csvfile:
                reader = csv.DictReader(
                    csvfile,
                    delimiter=self.delimiter,
                    quotechar=self.quotechar,
                )

                # Vérifier que le fichier a des colonnes
                if not reader.fieldnames:
                    self.logger.error("Le fichier CSV ne contient pas d'en-tête")
                    raise csv.Error("Le fichier CSV ne contient pas d'en-tête")

                self.logger.info(f"Colonnes détectées: {list(reader.fieldnames)}")

                # Itérer sur les lignes
                for row_number, row in enumerate(reader, start=1):
                    yield row

                self.logger.info(f"Fin de la lecture du fichier CSV ({row_number} lignes lues)")

        except csv.Error as e:
            self.logger.error(f"Erreur CSV à la lecture du fichier: {e}")
            raise
        except IOError as e:
            self.logger.error(f"Erreur d'entrée/sortie: {e}")
            raise

    def __enter__(self):
        """
        Context manager entry.

        Returns:
            L'instance de CSVReader
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit.

        Args:
            exc_type: Type de l'exception si une erreur s'est produite
            exc_val: Valeur de l'exception
            exc_tb: Traceback de l'exception
        """
        # Fermer le fichier si ouvert
        if self._file_handle is not None:
            self._file_handle.close()
            self._file_handle = None
