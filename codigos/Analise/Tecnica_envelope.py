import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter, find_peaks

# Substitua pelo caminho real do seu arquivo CSV
caminho_arquivo = 'C:/Users/amara/Desktop/PFC/banco de dados/saldavelcompesoxc.csv'

# Carregue os dados do arquivo CSV
dados = np.genfromtxt(caminho_arquivo, delimiter=',', skip_header=1)

# Defina a taxa de amostragem em Hz
taxa_amostragem = 440  # 440 Hz

# Defina o comprimento da janela
window_length = 1024

# Frequências correspondentes à FFT (parte positiva, excluindo 0 Hz e o próximo valor)
frequencias = np.fft.fftfreq(window_length, 1/taxa_amostragem)[2:window_length//2]

# Inicialize uma lista para armazenar os espectros de magnitude
espectros = []

# Aplique a janela de Hanning e a FFT aos dados
for i in range(0, len(dados), window_length):
    if i + window_length <= len(dados):
        janela = dados[i:i+window_length]
        janela_hanning = janela * np.hanning(window_length)
        espectro_hanning = np.fft.fft(janela_hanning)
        espectros.append(np.abs(espectro_hanning[2:window_length//2]))

# Converta a lista de espectros em um array numpy para facilitar a manipulação
espectros = np.array(espectros)

# Calcule a média dos espectros
espectro_medio = np.mean(espectros, axis=0)

# Etapa 3: Aplicação do filtro passa-banda
# Frequência central do filtro passa-banda (74.7 Hz)
frequencia_central = 74.7  # Hz

# Largura de banda do filtro passa-banda (ajuste conforme necessário)
largura_banda = 20  # Hz

# Calcule os coeficientes do filtro passa-banda
frequencia_normalizada = frequencia_central / (taxa_amostragem / 2)
largura_normalizada = largura_banda / (taxa_amostragem / 2)
b, a = butter(4, [frequencia_normalizada - largura_normalizada/2, frequencia_normalizada + largura_normalizada/2], btype='band')

# Aplique o filtro passa-banda aos dados
sinal_filtrado = lfilter(b, a, dados)

# Etapa 4: Demodulação do sinal
t = np.arange(0, len(sinal_filtrado)) / taxa_amostragem
sinal_demodulado = sinal_filtrado * np.cos(2 * np.pi * frequencia_central * t)

# Etapa 5: Cálculo do envelope do sinal
amplitude_envelope = np.abs(sinal_demodulado)

# Etapa 6: Suavização do envelope
janela_suavizacao = 100  # Tamanho da janela de suavização (ajuste conforme necessário)
envelope_suavizado = np.convolve(amplitude_envelope, np.ones(janela_suavizacao)/janela_suavizacao, mode='same')

# Etapa 7: Identificação de picos no envelope suavizado
picos, _ = find_peaks(envelope_suavizado, height=0.18)  # Ajuste o valor de 'height' conforme necessário

# FFT do sinal suavizado
espectro_suavizado = np.fft.fft(envelope_suavizado)

# Plot dos sinais em subplots separados
fig, axs = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

# Sinal Original
axs[0].plot(dados)
axs[0].set_title('Sinal Original')
axs[0].set_ylabel('Amplitude (m/s²)')
axs[0].grid(True)

# Sinal com Janela de Hanning
axs[1].plot(dados * np.hanning(len(dados)))
axs[1].set_title('Sinal com Janela de Hanning')
axs[1].set_xlabel('Amostra')
axs[1].set_ylabel('Amplitude')
axs[1].grid(True)

plt.show()

# Identificação de picos no espectro
picos, _ = find_peaks(np.abs(espectros[0]), height=3.23)  # Ajuste o valor de 'height' conforme necessário PARA IDENTIFICAR ESPECTROS DOMINANTES:

# Plotagem do espectro de frequência (parte positiva)
plt.figure(figsize=(10, 6))
plt.plot(frequencias, np.abs(espectro_medio), color='blue')

# Adição de marcadores para picos com valores
for pico in picos:
    plt.plot(frequencias[pico], np.abs(espectro_medio[pico]), 'ro', label=f'{np.abs(espectro_medio[pico]):.2f}')

plt.legend()

# Configurações de plotagem
plt.title('Espectro de Frequência após Janelamento (Parte Positiva) com Picos Identificados')
plt.xlabel('Frequência (Hz)')
plt.ylabel('Amplitude')
plt.grid(True)
plt.show()

# FFT do sinal suavizado
plt.figure(figsize=(10, 6))
plt.plot(frequencias, np.abs(espectro_suavizado[2:window_length//2]))
plt.title('Espectro do Sinal Suavizado')
plt.xlabel('Frequência (Hz)')
plt.ylabel('Amplitude')
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(sinal_filtrado)
plt.title('Sinal Filtrado')
plt.xlabel('Amostra')
plt.ylabel('Amplitude (m/s²)')
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(sinal_demodulado)
plt.title('Sinal Demodulado')
plt.xlabel('Amostra')
plt.ylabel('Amplitude (m/s²)')
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(amplitude_envelope)
plt.title('Envelope do Sinal')
plt.xlabel('Amostra')
plt.ylabel('Amplitude (m/s²)')
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(envelope_suavizado)
plt.plot(envelope_suavizado[picos], 'ro', label='Picos Identificados')
plt.title('Envelope Suavizado')
plt.xlabel('Amostra')
plt.ylabel('Amplitude do Envelope Suavizado (m/s²)')
plt.legend()
plt.grid(True)
plt.show()

# Exiba as amplitudes dos picos identificados
amplitudes_picos = envelope_suavizado[picos]
print('Amplitudes dos Picos:', amplitudes_picos)
