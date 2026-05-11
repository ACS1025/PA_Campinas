// Variável para armazenar os dados da tabela de veiculos.html
let dadosVeiculos = [];

// Função que carrega a tabela de veiculos.html
function carregarDadosVeiculos() {
    const urlVeiculos = 'Consultas/veiculos.html'; // Caminho do arquivo veiculos.html

    fetch(urlVeiculos)
        .then(response => response.text())
        .then(html => {
            // Cria um documento temporário para manipular o HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Encontra a tabela (ajuste conforme necessário)
            const tabela = doc.querySelector('table'); 

            if (tabela) {
                const linhas = tabela.querySelectorAll('tr');
                dadosVeiculos = [];

                // Itera sobre as linhas da tabela e extrai os dados
                linhas.forEach(linha => {
                    const colunas = linha.querySelectorAll('td');
                    if (colunas.length > 0) {
                        const placa = colunas[0].innerText.trim(); // Primeira coluna - Placa
                        const tipoVeiculo = colunas[1].innerText.trim(); // Segunda coluna - Tipo
                        
                        // Armazena as informações em um array
                        dadosVeiculos.push({ placa, tipoVeiculo });
                    }
                });
            }
        })
        .catch(error => console.error('Erro ao carregar o arquivo veiculos.html:', error));
}

// Função de busca da placa
function buscarPlacas(placaDigitada) {
    const listaPlaca = document.getElementById('lista-placa');
    listaPlaca.innerHTML = ''; // Limpa a lista de sugestões anteriores
    
    // Filtra as placas que correspondem ao texto digitado
    const resultados = dadosVeiculos.filter(veiculo => 
        veiculo.placa.toLowerCase().includes(placaDigitada.toLowerCase())
    );

    // Exibe as sugestões
    resultados.forEach(veiculo => {
        const li = document.createElement('li');
        li.innerText = `Placa: ${veiculo.placa} - Tipo: ${veiculo.tipoVeiculo}`;
        li.addEventListener('click', function() {
            // Preenche o campo de entrada com a placa selecionada
            document.getElementById('doc_placa').value = veiculo.placa;
            listaPlaca.innerHTML = ''; // Limpa a lista após a seleção
        });
        listaPlaca.appendChild(li);
    });
}

// Carregar os dados assim que a página for carregada
document.addEventListener('DOMContentLoaded', carregarDadosVeiculos);
