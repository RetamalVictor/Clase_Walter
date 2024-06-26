import torch
import torch.nn as nn

class ParallelModel(nn.Module):
    """
    Esta version utiliza el ultimo dia de cada trozo de la serie
    
    """
                        # m  (numero stocks)               # k             
    def __init__(self, input_features=10, hidden_size=20, output_size=1, num_layers=1):
        super(ParallelModel, self).__init__()
        # LSTM layer
        self.lstm = nn.LSTM(input_size=input_features, hidden_size=hidden_size, batch_first=True, num_layers=num_layers)
        # Linear layer en paralelo al LSTM
        self.mlp = nn.Linear(in_features=input_features, out_features=hidden_size)
        # Capa lineal que recibe la concatenación de las salidas de LSTM y la capa lineal
        self.output_mlp = nn.Linear(in_features=2*hidden_size, out_features=output_size)
                                                # 2k                        # scalar
    def forward(self, x):
        # x debe tener la forma (batch_size, seq_lenght, input_features)
        # Salida del LSTM
        lstm_out, _ = self.lstm(x)  # lstm_out tiene la forma (batch_size, seq_lenght, hidden_size)
        # Tomamos solo la última salida del LSTM para cada secuencia
        lstm_out = lstm_out[:, -1, :]  # Ahora lstm_out tiene la forma (batch_size, hidden_size) (batch_size, 20)

        # Salida de la capa lineal
        #opcion 1: solo el ultimo dia de la sequencia
        mlp_output = self.mlp(x[:, -1, :])  # Usamos solo el último elemento de la secuencia 
        # output tiene dimension (batch_size, hidden_size) (b_s, 20)
        
        # Concatenamos las salidas del LSTM y la capa lineal
        combined_output = torch.cat((lstm_out, mlp_output), dim=1) 
        # tiene dimension (b_s, k*2) (b_s, 40)

        # Pasamos la salida combinada a través de la capa lineal final
        final_output = self.output_mlp(combined_output)

        return final_output # es un scalar

class ParallelModel_2(nn.Module):
    """
    Esta version hace aplanamiento de todo el trocito de serie temporal
    """
    def __init__(self, input_features=10, hidden_size=20, output_size=1, num_layers=1):
        super(ParallelModel_2, self).__init__()
        # LSTM layer
        self.lstm = nn.LSTM(input_size=input_features, hidden_size=hidden_size, batch_first=True, num_layers=num_layers)
        # Linear layer en paralelo al LSTM
        # La capa lineal ahora espera una entrada aplanada de tamaño seq_length * input_features
                                            # 5 * 10 = 50
        self.linear = nn.Linear(in_features=5 * input_features, out_features=hidden_size)  # Asumiendo seq_length=5
        # Capa lineal que recibe la concatenación de las salidas de LSTM y la capa lineal
        self.output_linear = nn.Linear(in_features=2*hidden_size, out_features=output_size)

    def forward(self, x):
        # x debe tener la forma (seq_length, batch_size, input_features)
        lstm_out, _ = self.lstm(x)  # lstm_out tiene la forma (batch_size, seq_lenght, hidden_size)
        # Tomamos solo la última salida del LSTM para cada secuencia
        lstm_out = lstm_out[:, -1, :]  # Ahora lstm_out tiene la forma (batch_size, hidden_size)

        # Aplanamos todo el chunk de la serie temporal antes de pasarlo a la capa lineal
        x_flattened = x.view(x.shape[0], -1)  # Cambiamos la forma a (batch_size, seq_length * input_features)
        mlp_output = self.linear(x_flattened)  # mlp_output tiene la forma (batch_size, hidden_size)

        # Concatenamos las salidas del LSTM y la capa lineal
        combined_output = torch.cat((lstm_out, mlp_output), dim=1)  # combined_output tiene la forma (batch_size, 2*hidden_size)

        # Pasamos la salida combinada a través de la capa lineal final
        final_output = self.output_linear(combined_output)

        return final_output

if __name__ == "__main__":
    # Ejemplo de uso
    model = ParallelModel()
    input_tensor = torch.rand(32, 5, 10)  # batch_size=32, seq_length=5, input_features=10
    output = model(input_tensor)
    print(output.shape)  # Debería ser (32, 1) para un batch_size de 32 y un output_size de 1


    # Ejemplo de uso
    model = ParallelModel_2()
    input_tensor = torch.rand(32, 5, 10)  # batch_size=32, seq_length=5, input_features=10
    output = model(input_tensor)
    print(output.shape)  # Debería ser (32, 1) para un batch_size de 32 y un output_size de 1
