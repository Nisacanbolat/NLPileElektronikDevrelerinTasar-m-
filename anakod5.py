import json
import os
import re
import subprocess
import sys
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
import math
 # varsa modül ismini senin dosya adına göre ayarla


class CircuitDesigner:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")  # NLP modeli
        except OSError:
            print("Spacy modeli yüklenemedi. Basit moda geçiliyor...")
            self.nlp = None
        
        self.config = self.load_config()
        self.ensure_directories()
        self.dataset = self.load_dataset()
        
    def load_config(self):
        """Yapılandırma ayarlarını yükler"""
        default_config = {
            "default_resistor": "10k",
            "default_capacitor": "1u",
            "default_voltage": "15",
            "default_gain": "10",
            "default_cutoff": "1000",  # 1 kHz default
            "default_time_constant": "1ms",  # Türev/integral alıcılar için
            "output_dir": "circuit_outputs",
            "latex_templates_dir": "latex_codes"
        }
        
        try:
            with open("config.json", "r") as f:
                return {**default_config, **json.load(f)}
        except FileNotFoundError:
            return default_config

    def ensure_directories(self):
        """Gerekli dizinleri oluşturur"""
        Path(self.config["output_dir"]).mkdir(exist_ok=True)
        Path(self.config["latex_templates_dir"]).mkdir(exist_ok=True)

    def load_dataset(self):
        """Devre datasetini yükler"""
        try:
            with open("dataset2.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Dataset yükleme hatası: {e}")
            return []

    def normalize_turkish_text(self, text):
        """Türkçe karakterleri standartlaştır ve küçük harfe çevir"""
        if not text:
            return ""
        
        # Türkçe karakter dönüşüm tablosu
        tr_map = {
            'İ': 'i', 'I': 'ı', 'Ü': 'ü', 'Ö': 'ö', 'Ç': 'ç', 'Ş': 'ş', 'Ğ': 'ğ',
            'i': 'i', 'ı': 'ı', 'ü': 'ü', 'ö': 'ö', 'ç': 'ç', 'ş': 'ş', 'ğ': 'ğ'
        }
        
        # Metni küçült ve Türkçe karakterleri standartlaştır
        result = ''
        for char in text.lower():
            result += tr_map.get(char, char)
        
        return result

    def preprocess_text(self, text):
        """Metni NLP için hazırlar"""
        if self.nlp:
            doc = self.nlp(text.lower())
            return " ".join([token.lemma_ for token in doc if not token.is_stop])
        else:
            return text.lower()

    def find_best_match(self, user_input):
        """Kullanıcı girdisine en uygun devreyi bulur"""
        if not self.dataset:
            return None

        processed_input = self.preprocess_text(user_input)
        inputs = [self.preprocess_text(item["input"]) for item in self.dataset]
        
        for i, item in enumerate(inputs):
         if processed_input.strip().lower() == item.strip().lower():
             return self.dataset[i]

        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([processed_input] + inputs)
        similarities = cosine_similarity(vectors[0], vectors[1:])
        best_match_idx = similarities.argmax()
        
        if similarities[0][best_match_idx] < 0.3:
            print("Uyarı: Düşük benzerlik skoru, en yakın eşleşme kullanılıyor")
        
        return self.dataset[best_match_idx]

    def check_circuit_type(self, circuit_type, search_term):
        """Türkçe karakter duyarsız devre tipi kontrolü"""
        normalized_circuit_type = self.normalize_turkish_text(circuit_type)
        normalized_search_term = self.normalize_turkish_text(search_term)
        
        return normalized_search_term in normalized_circuit_type

    def parse_numeric_value(self, value_str):
        """Kullanıcı girdisini sayısal değere çevirir"""
        value_str = re.sub(r'[^0-9kKMuμnp.]', '', value_str.strip())
        
        multipliers = {
            'k': 1e3, 'K': 1e3, 
            'M': 1e6, 
            'u': 1e-6, 'μ': 1e-6, 
            'n': 1e-9, 
            'p': 1e-12
        }
        
        match = re.match(r"([\d.]+)([kKMuμnp]?)", value_str)
        if not match:
            raise ValueError(f"Geçersiz değer formatı: {value_str}")
        
        number, unit = match.groups()
        number = float(number)
        return number * multipliers.get(unit, 1)

    def get_circuit_parameters(self, circuit_type):
        """İstenen parametre değerlerini kullanıcıdan alır ve hesaplamalar yapar"""
        params = {}
        print(f"\n[{circuit_type} Parametreleri]")
        
        try:
            if self.check_circuit_type(circuit_type, "tersleyici"):
                gain_str = input(f"İstenen kazanç değeri [{self.config['default_gain']}x]: ").strip() or self.config['default_gain']
                gain = float(gain_str)
                params["R1"] = self.parse_numeric_value(self.config["default_resistor"])
                params["R2"] = params["R1"] * abs(gain)
                params["GainFormula"] = r"-\frac{R_2}{R_1}"
                params["GainValue"] = f"{-gain:.2f}"
                print(f"Hesaplanan R1: {self.format_resistance(params['R1'])}")
                print(f"Hesaplanan R2: {self.format_resistance(params['R2'])}")
                print(f"Kazanç: {-gain:.2f}x")
                
            elif self.check_circuit_type(circuit_type, "terslemeyen"):
                gain_str = input(f"İstenen kazanç değeri [{self.config['default_gain']}x]: ").strip() or self.config['default_gain']
                gain = float(gain_str)
                params["R1"] = self.parse_numeric_value(self.config["default_resistor"])
                params["R2"] = params["R1"] * (gain - 1)
                params["GainFormula"] = r"1 + \frac{R_2}{R_1}"
                params["GainValue"] = f"{gain:.2f}"
                print(f"Hesaplanan R1: {self.format_resistance(params['R1'])}")
                print(f"Hesaplanan R2: {self.format_resistance(params['R2'])}")
                print(f"Kazanç: {gain:.2f}x")

            elif self.check_circuit_type(circuit_type, "alçak geçiren filtre") or self.check_circuit_type(circuit_type, "yüksek geçiren filtre"):
                cutoff_str = input(f"İstenen kesim frekansı [{self.config['default_cutoff']} Hz]: ").strip() or self.config['default_cutoff']
                cutoff = float(cutoff_str)
                params["C"] = self.parse_numeric_value(self.config["default_capacitor"])
                params["R"] = 1 / (2 * math.pi * cutoff * params["C"])
                params["Cutoff"] = f"{cutoff:.2f} Hz"
                print(f"Hesaplanan R: {self.format_resistance(params['R'])}")
                print(f"Hesaplanan C: {self.format_capacitance(params['C'])}")
                print(f"Kesim Frekansı: {cutoff:.2f} Hz")
                
            elif self.check_circuit_type(circuit_type, "toplayıcı"):
                gain1_str = input(f"Birinci giriş için kazanç [-{self.config['default_gain']}]: ").strip() or f"-{self.config['default_gain']}"
                gain2_str = input(f"İkinci giriş için kazanç [-{self.config['default_gain']}]: ").strip() or f"-{self.config['default_gain']}"
                gain1 = float(gain1_str)
                gain2 = float(gain2_str)
                params["Rf"] = self.parse_numeric_value(self.config["default_resistor"])
                params["R1"] = params["Rf"] / abs(gain1)
                params["R2"] = params["Rf"] / abs(gain2)
                gain_formula = r"-\left(\frac{R_f}{R_1}V_1 + \frac{R_f}{R_2}V_2\right)"
                params["GainFormula"] = gain_formula
                print(f"Hesaplanan Rf: {self.format_resistance(params['Rf'])}")
                print(f"Hesaplanan R1: {self.format_resistance(params['R1'])}")
                print(f"Hesaplanan R2: {self.format_resistance(params['R2'])}")
                print(f"Çıkış formülü: Vout = {gain_formula}")

            elif self.check_circuit_type(circuit_type, "schmitt"):
                vut_str = input(f"İstenen üst eşik değeri [5 V]: ").strip() or "5"
                vut = float(vut_str)
                params["Vcc"] = self.parse_numeric_value(self.config["default_voltage"])
                params["R1"] = self.parse_numeric_value(self.config["default_resistor"])
                params["R2"] = params["R1"] * (vut / (params["Vcc"] - vut))
                params["Vut"] = f"{vut:.2f} V"
                params["Vlt"] = f"{-vut:.2f} V"
                print(f"Hesaplanan R1: {self.format_resistance(params['R1'])}")
                print(f"Hesaplanan R2: {self.format_resistance(params['R2'])}")
                print(f"Üst Eşik: {vut:.2f} V, Alt Eşik: {-vut:.2f} V")

            elif self.check_circuit_type(circuit_type, "gerilim izleyici"):
                params["GainFormula"] = "1"
                params["GainValue"] = "1.00"
                print("Gerilim İzleyici için kazanç: 1.00")

            elif self.check_circuit_type(circuit_type, "türev alıcı"):
                tau_str = input(f"İstenen zaman sabiti (RC) [{self.config['default_time_constant']}]: ").strip() or self.config['default_time_constant']
                tau = self.parse_numeric_value(tau_str)
                params["R"] = self.parse_numeric_value(self.config["default_resistor"])
                params["C"] = tau / params["R"]
                params["Formula"] = r"V_{out} = -RC\frac{dV_{in}}{dt}"
                print(f"Hesaplanan R: {self.format_resistance(params['R'])}")
                print(f"Hesaplanan C: {self.format_capacitance(params['C'])}")
                print(f"Zaman Sabiti (τ): {tau*1000:.2f} ms")
                
            elif self.check_circuit_type(circuit_type, "integral alıcı") or self.check_circuit_type(circuit_type, "İntegral alıcı"):
                tau_str = input(f"İstenen zaman sabiti (RC) [{self.config['default_time_constant']}]: ").strip() or self.config['default_time_constant']
                tau = self.parse_numeric_value(tau_str)
                params["R"] = self.parse_numeric_value(self.config["default_resistor"])
                params["C"] = tau / params["R"]
                params["Rf"] = params["R"] * 10  # DC ofset için
                params["Formula"] = r"V_{out} = -\frac{1}{RC}\int V_{in}dt"
                print(f"Hesaplanan R: {self.format_resistance(params['R'])}")
                print(f"Hesaplanan C: {self.format_capacitance(params['C'])}")
                print(f"Hesaplanan Rf: {self.format_resistance(params['Rf'])}")
                print(f"Zaman Sabiti (τ): {tau*1000:.2f} ms")
                
            elif self.check_circuit_type(circuit_type, "fark yükselteci"):
                gain_str = input(f"İstenen kazanç değeri [{self.config['default_gain']}x]: ").strip() or self.config['default_gain']
                gain = float(gain_str)
                params["R1"] = self.parse_numeric_value(self.config["default_resistor"])
                params["R3"] = params["R1"] * gain
                params["R2"] = params["R1"]
                params["R4"] = params["R3"]
                params["GainFormula"] = r"\frac{R3}{R1}"
                params["GainValue"] = f"{gain:.2f}"
                print(f"Hesaplanan R1: {self.format_resistance(params['R1'])}")
                print(f"Hesaplanan R2: {self.format_resistance(params['R2'])}")
                print(f"Hesaplanan R3: {self.format_resistance(params['R3'])}")
                print(f"Hesaplanan R4: {self.format_resistance(params['R4'])}")
                print(f"Kazanç: {gain:.2f}x")

            params = self.format_parameters(params)
            
        except Exception as e:
            print(f"Parametre hesaplama hatası: {e}")
        
        return params

    def format_resistance(self, value):
        """Direnç değerini okunaklı formata çevirir"""
        if value >= 1e6:
            return f"{value/1e6:.2f} MΩ"
        elif value >= 1e3:
            return f"{value/1e3:.2f} kΩ"
        else:
            return f"{value:.2f} Ω"
            
    def format_capacitance(self, value):
        """Kapasitans değerini okunaklı formata çevirir"""
        if value >= 1e-3:
            return f"{value*1e3:.2f} mF"
        elif value >= 1e-6:
            return f"{value*1e6:.2f} μF"
        elif value >= 1e-9:
            return f"{value*1e9:.2f} nF"
        else:
            return f"{value*1e12:.2f} pF"

    def format_parameters(self, params):
        """Parametreleri LaTeX formatına dönüştürür"""
        formatted = {}
        for key, value in params.items():
            if isinstance(value, (int, float)):
                if key.startswith('R'):
                    if value >= 1e6:
                        formatted[key] = f"{value/1e6:.1f}\\\\ M\\\\Ohm"
                    elif value >= 1e3:
                        formatted[key] = f"{value/1e3:.1f}\\\\ k\\\\Ohm"
                    else:
                        formatted[key] = f"{value:.1f}\\\\ \\\\Ohm"
                elif key.startswith('C'):
                    if value >= 1e-3:
                        formatted[key] = f"{value*1e3:.1f}\\\\ mF"
                    elif value >= 1e-6:
                        formatted[key] = f"{value*1e6:.1f}\\\\ \\\\mu F"
                    elif value >= 1e-9:
                        formatted[key] = f"{value*1e9:.1f}\\\\ nF"
                    else:
                        formatted[key] = f"{value*1e12:.1f}\\\\ pF"
                elif key.startswith('V'):
                    formatted[key] = f"{value:.1f}\\\\ V"
            else:
                formatted[key] = str(value)
        return formatted

    def generate_latex_code(self, circuit_type, parameters):
        """LaTeX devre şeması kodunu oluşturur"""
        filename = circuit_type.lower().replace(' ', '_')
        tr_chars = {'ü':'u', 'ğ':'g', 'ş':'s', 'ı':'i', 'ö':'o', 'ç':'c'}
        for char, replacement in tr_chars.items():
            filename = filename.replace(char, replacement)
        filename += '.tex'
        
        template_file = Path(self.config["latex_templates_dir"]) / filename
        
        if not template_file.exists():
            print(f"\nHATA: Şu konumda şablon dosyası bulunamadı: {template_file}")
            print("Mevcut şablon dosyaları:")
            for f in Path(self.config["latex_templates_dir"]).glob('*.tex'):
                print(f" - {f.name}")
            return None
        
        with open(template_file, "r", encoding="utf-8") as f:
            latex_code = f.read()
        
        for param, value in parameters.items():
            latex_code = latex_code.replace(f"<<{param}>>", value)
        
        return latex_code

    def compile_latex(self, latex_code, filename):
        """LaTeX kodunu PDF'e derler"""
        output_dir = Path(self.config["output_dir"])
        tex_file = output_dir / f"{filename}.tex"
        
        try:
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(latex_code)
            
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", f"-output-directory={output_dir}", tex_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                pdf_path = output_dir / f"{filename}.pdf"
                print(f"\nPDF başarıyla oluşturuldu: {pdf_path}")
                self.open_pdf(pdf_path)
                return True
            else:
                print("\nLaTeX derleme hatası:")
                print(result.stderr)
                return False
        except Exception as e:
            print(f"\nPDF oluşturma hatası: {e}")
            return False

    def open_pdf(self, pdf_path):
        """Oluşturulan PDF'i açar"""
        if sys.platform == "win32":
            os.startfile(pdf_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", pdf_path])
        else:
            subprocess.run(["xdg-open", pdf_path])

    def run(self):
        """Ana uygulama akışını çalıştırır"""
        print("\nOPAMP DEVRE TASARIM SİSTEMİ")
        print("===========================")
        print("Desteklenen Devreler: Tersleyici Yükselteç, Terslemeyen Yükselteç,")
        print("Toplayıcı Yükselteç, Alçak Geçiren Filtre, Yüksek Geçiren Filtre,")
        print("Schmitt Trigger, Gerilim İzleyici, Türev Alıcı, Integral Alıcı,")
        print("Fark Yükselteci\n")
        
        user_input = input("Hangi opamp devresini oluşturmak istersiniz? ").strip()
        if not user_input:
            print("Geçersiz giriş!")
            return
        
        circuit = self.find_best_match(user_input)
        if not circuit:
            print("Eşleşen devre bulunamadı!")
            return
        
        print(f"\nSeçilen Devre: {circuit['circuit_type']}")
        params = self.get_circuit_parameters(circuit["circuit_type"])
        
        latex_code = self.generate_latex_code(circuit["circuit_type"], params)
        if not latex_code:
            return
        
        if input("\nLaTeX kodunu görmek ister misiniz? (e/h): ").lower() == 'e':
            print("\n" + "="*50)
            print(latex_code)
            print("="*50 + "\n")
        
        filename = circuit["circuit_type"].lower().replace(' ', '_')
        tr_chars = {'ü':'u', 'ğ':'g', 'ş':'s', 'ı':'i', 'ö':'o', 'ç':'c'}
        for char, replacement in tr_chars.items():
            filename = filename.replace(char, replacement)
        
        if self.compile_latex(latex_code, filename):
            print("\nBaşarıyla tamamlandı!")

if __name__ == "__main__":
    designer = CircuitDesigner()
    designer.run()