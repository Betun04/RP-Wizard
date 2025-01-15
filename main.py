import os
from zipfile import ZipFile
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFileDialog
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PIL import Image
import io, shutil

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RP-Wizard")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QPixmap("icon.ico"))

        self.packDir = ""

        # Crear el widget de solapas (tabs)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Agregar las secciones
        self.tabs.addTab(self.create_item_texture_tab(), "Texturas de Ítems")

        self.texture_files = []  # Lista de archivos de texturas
        self.zip_file = None  # Archivo ZIP abierto (si es necesario)

    def create_item_texture_tab(self):
        """Crea la sección para cambiar texturas de ítems."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(30)  # Sin espaciado vertical
        layout.setContentsMargins(10, 10, 10, 30)  # Márgenes uniformes

        # Botón para cargar un pack de texturas
        load_pack_button = QPushButton("Cargar Pack de Texturas")
        load_pack_button.clicked.connect(self.load_texture_pack)
        layout.addWidget(load_pack_button)

        # Diseño horizontal para ComboBox y botón
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)

        self.combo_box = QComboBox()
        self.combo_box.setPlaceholderText("Selecciona una textura")
        self.combo_box.currentIndexChanged.connect(self.update_preview)  # Conexión correcta al método
        row_layout.addWidget(self.combo_box, 2)  # Proporción ajustada para mayor ancho

        self.replace_button = QPushButton("Reemplazar Textura")
        self.replace_button.setEnabled(False)
        self.replace_button.clicked.connect(self.replace_texture)
        row_layout.addWidget(self.replace_button, 1)

        layout.addLayout(row_layout)

        # Espaciador para empujar el previsualizador hacia abajo
        layout.addStretch(0)

        # Previsualización de texturas
        self.preview_label = QLabel("Vista previa")
        self.preview_label.setFixedSize(400, 400)  # Aumentar el tamaño de la vista previa
        self.preview_label.setStyleSheet("border: 1px solid black;")
        self.preview_label.setAlignment(Qt.AlignCenter)  # Centrar contenido de la imagen
        layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)

        # Establecer el diseño
        tab.setLayout(layout)
        return tab

    def load_texture_pack(self):
        """Carga un pack de texturas y lista los archivos de ítems en el ComboBox."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Pack de Texturas", "", "Archivos ZIP (*.zip);;Carpetas (*)")
        if not file_path:
            return

        self.texture_files.clear()
        self.combo_box.clear()

        # Leer el pack de texturas
        if file_path.endswith(".zip"):
            self.zip_file = ZipFile(file_path, 'r')
            for file_name in self.zip_file.namelist():
                if file_name.startswith("assets/minecraft/textures/item/") and file_name.endswith(".png"):
                    self.texture_files.append(file_name)
        else:
            for root, _, files in os.walk(file_path):
                for file_name in files:
                    if root.endswith("textures/item") and file_name.endswith(".png"):
                        self.texture_files.append(os.path.join(root, file_name))

        #Ordenar la lista de texturas
        self.texture_files.sort()

        # Poblar el ComboBox con los archivos encontrados
        for texture in self.texture_files:
            item_name = os.path.splitext(os.path.basename(texture))[0]  # Nombre sin extensión
            item_name = item_name.replace("_"," ").title()  # Reemplazar guiones bajos y capitalizar
            self.combo_box.addItem(item_name)

        # Habilitar el botón de reemplazo si hay elementos
        self.replace_button.setEnabled(bool(self.texture_files))

        # Actualizar la vista previa con la primera textura cargada
        self.update_preview()

    def update_preview(self):
        """Actualiza la vista previa de la textura seleccionada."""
        selected_texture_index = self.combo_box.currentIndex()
        if selected_texture_index == -1:
            self.preview_label.clear()
            return

        texture_path = self.texture_files[selected_texture_index]
        pixmap = self.load_pixmap(texture_path)
        if pixmap:
            self.preview_label.setPixmap(pixmap)

    def replace_texture(self):
        """Permite seleccionar una nueva textura para reemplazar la seleccionada."""
        selected_texture_index = self.combo_box.currentIndex()
        if selected_texture_index == -1:
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Nueva Textura", "", "Imágenes (*.png)")
        if file_path:
            print(f"Reemplazando {self.combo_box.currentText()} con {file_path}")
            
            # Cambiar el archivo de la textura en el zip
            if self.zip_file:
                texture_path = self.texture_files[selected_texture_index]
                self.reemplazar_archivo_en_zip(self.zip_file.filename,texture_path,file_path)

            base_path = os.path.dirname(__file__)
            ruta_imagen = os.path.join(base_path, file_path.split("/")[-1])

            pixmap = QPixmap(ruta_imagen)
            if pixmap.isNull():
                print(f"Error: No se pudo cargar la imagen desde '{ruta_imagen}'.")
                self.preview_label.setText("No se pudo cargar la imagen.")
            else:
                self.preview_label.setPixmap(pixmap)

    def load_pixmap(self, texture_path):
        """Carga una imagen como QPixmap desde un archivo o archivo ZIP sin perder calidad."""
        try:
            if self.zip_file:  # Si es un archivo ZIP
                with self.zip_file.open(texture_path) as file:
                    img_data = file.read()
                    img = Image.open(io.BytesIO(img_data))
            else:  # Si es una ruta de archivo
                img = Image.open(texture_path)

            # Redimensionar manteniendo la relación de aspecto, pero sin suavizado (pixel art)
            img = img.resize((400, 400), Image.NEAREST)  # Usar 'NEAREST' para pixel art

            img.save("temp_preview.png")  # Guardar temporalmente para cargarla
            pixmap = QPixmap("temp_preview.png")
            os.remove("temp_preview.png")  # Eliminar archivo temporal
            return pixmap

        except Exception as e:
            print(f"Error al cargar la imagen: {e}")
            return None

    def reemplazar_archivo_en_zip(self, zip, archivo_a_reemplazar, nuevo_archivo):
        zip_temporal = zip + '.tmp'

        with ZipFile(zip, 'r') as zip_original:
            with ZipFile(zip_temporal, 'w') as zip_nuevo:
                for item in zip_original.infolist():
                    if item.filename != archivo_a_reemplazar:
                        zip_nuevo.writestr(item, zip_original.read(item.filename))
                zip_nuevo.write(nuevo_archivo, archivo_a_reemplazar)

        # Cerrar todos los archivos antes de manipularlos
        shutil.move(zip_temporal, zip)
        print(f"Archivo '{archivo_a_reemplazar}' reemplazado exitosamente en '{zip}'.") 

# Crear la aplicación y mostrar la ventana
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
