async function carregarCSV() {
    const url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQJmWx2vRWfkLgc2z4mdbsGkXA3Y5F2dViZffq4mvEwP1q7MBXPvp7Wg2TZU8Wrng/pub?output=csv"; // Substitua pelo seu link correto
    
    try {
        const resposta = await fetch(url);
        const texto = await resposta.text();
        
        // Verifica se o CSV foi carregado corretamente
        if (!texto) {
            console.error("Erro: CSV vazio ou não carregado corretamente.");
            return;
        }

        const linhas = texto.trim().split("\n").map(linha => linha.split(",")); 

        let tabelaHTML = "<table border='1'><tr>";

        // Criar cabeçalhos
        linhas[0].forEach(coluna => tabelaHTML += `<th>${coluna}</th>`);
        tabelaHTML += "</tr>";

        // Criar linhas de dados
        for (let i = 1; i < linhas.length; i++) {
            tabelaHTML += "<tr>";
            linhas[i].forEach(celula => tabelaHTML += `<td>${celula}</td>`);
            tabelaHTML += "</tr>";
        }

        tabelaHTML += "</table>";
        document.getElementById("tabela").innerHTML = tabelaHTML;
    } catch (erro) {
        console.error("Erro ao carregar CSV:", erro);
    }
}

// Carregar os dados ao abrir a página
carregarCSV();
