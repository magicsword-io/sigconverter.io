// initialize select dropdowns
new TomSelect("#select-backend", {
  controlInput: null,
  valueField: "value",
  labelField: "label",
  sortField: {
    field: "value",
    direction: "asc"
  }
});
new TomSelect("#select-format", {
  controlInput: null,
  valueField: "value",
  labelField: "label"
});
new TomSelect("#select-pipeline", {
  allowEmptyOption: true,
  plugins: ["remove_button", "checkbox_options"],
  persist: false,
  hidePlaceholder: true,
  searchField: "value",
  valueField: "value",
  labelField: "label"
});

// initial stuff todo when page is loaded
window.onload = function () {
  // Get the fragment section from the current URL, without the '#' character
  const fragment = window.location.hash.substring(1);

  // Split the hash into key-value pair strings
  const pairs = fragment.split('&');

  // Parse each pair into a key and a value and store them in a map
  const urlParameter = new Map();
  pairs.forEach(function(pair) {
    const [key, value] = pair.split('=');
    // If both key and value are present, decode and store them
    if (key && value) {
      urlParameter.set(decodeURIComponent(key), decodeURIComponent(value));
    }
  });
  
  // check if hideEditor parameter is in url
  if(urlParameter.has('hideEditor')){
    let hideEditor = urlParameter.get('hideEditor')
    if(hideEditor == 1){
      document.getElementById("rule-section").style.display = "none"
      document.getElementById("rule-grid").setAttribute("class", "")
    }
  }

  // check if rule parameter is in url
  if(urlParameter.has('rule')){
    let rule = atob(urlParameter.get('rule'));
    sigmaJar.updateCode(rule)
  }

  // check if pipelineYml parameter is in url
  if(urlParameter.has('pipelineYml')){
    let pipelineYml = atob(urlParameter.get('pipelineYml'));
    pipelineJar.updateCode(pipelineYml)
  }

  let backendSelect = document.getElementById("select-backend");
  // get parameter backend from url and check if it's a valid option
  if(urlParameter.has('backend') && backendSelect.querySelectorAll('option[value$="' + urlParameter.get('backend') + '"]').length > 0) {
    // select item in dropdown
    backendSelect.tomselect.addItem(urlParameter.get('backend'));
  }
  else { 
    // select splunk backend as default
    backendSelect.tomselect.addItem("splunk");
  }

  // only show formats for selected backend
  filterFormatOptions();

  // get parameter format and select item in dropdown
  let formatSelect = document.getElementById("select-format");
  if(urlParameter.has('format')) {
    formatSelect.tomselect.addItem(urlParameter.get('format'));
  }

  // only show pipelines available for selected backend
  filterPipelineOptions();

  let pipelineSelect = document.getElementById("select-pipeline");
  if(urlParameter.has('pipeline')) {
    const pipelineValues = urlParameter.get('pipeline').split(';');
    pipelineValues.forEach(function(value) {
      pipelineSelect.tomselect.addItem(value);
    });
  }

  // load cli command
  generateCli();
  // inital conversion of example rule
  convert(sigmaJar.toString(), pipelineJar.toString());
};

// define onchange handler for select dropdowns
document.getElementById("select-backend").onchange = function () {
  filterFormatOptions();
  filterPipelineOptions();
  generateCli();
  convert(sigmaJar.toString(), pipelineJar.toString());
};

document.getElementById("select-format").onchange = function () {
  generateCli();
  convert(sigmaJar.toString(), pipelineJar.toString());
};

document.getElementById("select-pipeline").onchange = function () {
  generateCli();
  convert(sigmaJar.toString(), pipelineJar.toString());
};

// define onclick handler for buttons
document.getElementById("query-copy-btn").onclick = function () {
  copyQuery();
};
document.getElementById("rule-share-btn").onclick = function () {
  generateShareLink();
};
document.getElementById("tab-rule").onclick = function () {
  showTab("tab-rule", "rule-code");
};
document.getElementById("tab-pipeline").onclick = function () {
  showTab("tab-pipeline", "pipeline-code");
};

function showTab(tabId, codeId){
  var i, tabcontent, tablinks;
  var tab = document.getElementById(tabId);
  var code = document.getElementById(codeId);
  
  // hide all code areas
  tabcontent = document.getElementsByClassName("tab-code");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].classList.add('hidden');
  }

  // remove color from all tabs
  tablinks = document.getElementsByClassName("file-tab");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].classList.remove('bg-sigma-blue');
    tablinks[i].classList.remove('text-sigma-dark');
  }

  // display the selected code area
  code.parentElement.classList.remove('hidden');

  // change color of tab button to indicate selected code area
  tab.classList.add('bg-sigma-blue');
  tab.classList.add('text-sigma-dark');
}

function generateShareLink() {
  let backend = getSelectValue("select-backend");
  let format = getSelectValue("select-format");
  let pipelines = getSelectValue("select-pipeline");
  let rule = encodeURIComponent(btoa(sigmaJar.toString()));
  let pipelineYml = encodeURIComponent(btoa(pipelineJar.toString()));

  // generate link with parameters
  let shareParams =  "#backend=" + backend + "&format=" + format + "&pipeline=" + pipelines.join(";") + "&rule=" + rule + "&pipelineYml=" + pipelineYml;
  let shareUrl = location.protocol + "//" + location.host + "/" + shareParams;
  window.history.pushState({}, null, shareParams);
  
  // copy link for sharing to clipboard
  navigator.clipboard.writeText(shareUrl);

  // toggle color for user feedback
  var ruleShareBtn = document.getElementById("rule-share-btn");
  ruleShareBtn.classList.toggle("text-sigma-blue");
  ruleShareBtn.classList.toggle("text-green-400");

  setTimeout(function () {
    ruleShareBtn.classList.toggle("text-sigma-blue");
    ruleShareBtn.classList.toggle("text-green-400");
  }, 1200);
}

function copyQuery() {
  let queryCode = document.getElementById("query-code");
  navigator.clipboard.writeText(queryCode.value);

  // toggle color for user feedback
  var queryCopyBtn = document.getElementById("query-copy-btn");
  queryCopyBtn.classList.toggle("text-sigma-blue");
  queryCopyBtn.classList.toggle("text-green-400");

  setTimeout(function () {
    queryCopyBtn.classList.toggle("text-sigma-blue");
    queryCopyBtn.classList.toggle("text-green-400");
  }, 1200);
}

function focusSelect(elementId) {
  document.getElementById(elementId).focus();
}

function getSelectValue(elementId) {
  let select = document.getElementById(elementId);
  let tomSelect = select.tomselect;
  return tomSelect.getValue();
}

function generateCli() {
  let cliCode = document.getElementById("cli-code");
  let backend = getSelectValue("select-backend");
  let format = getSelectValue("select-format");
  let pipelines = getSelectValue("select-pipeline");

  cliCommand = "sigma convert";
  if (pipelines.length === 0 && pipelineJar.toString().length == 0) {
    cliCommand = cliCommand + " --without-pipeline ";
  }
  pipelines.forEach((e) => {
    cliCommand = cliCommand + " -p " + e;
  });

  if(pipelineJar.toString().length > 0){
    cliCommand = cliCommand + " -p pipeline.yml";
  }

  cliCommand = cliCommand + " -t " + backend + " -f " + format + " rule.yml";
  cliCode.innerHTML = cliCommand;
  Prism.highlightElement(cliCode); // rerun code highlighting
}

function convert(sigmaRule, customPipeline) {
  let queryCode = document.getElementById("query-code");

  let backend = getSelectValue("select-backend");
  let format = getSelectValue("select-format");
  let pipelines = getSelectValue("select-pipeline");
  
  // create json object
  const params = {
    rule: btoa(sigmaRule),
    pipelineYml: btoa(customPipeline),
    pipeline: pipelines,
    target: backend,
    format: format
  };

  // send post request
  const xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function (e) {
    if (xhr.readyState === 4) {
      if (xhr.status === 200) {
        // write converted query to output code area
        queryCode.innerHTML = xhr.response;
        queryCode.value = xhr.response;
        Prism.highlightElement(queryCode); // rerun code highlighting
      } else if (xhr.status === 400) {
        queryCode.innerHTML = xhr.response;
      } else if (xhr.status === 500) {
        queryCode.innerHTML = "Error: Something went wrong";
      }
    }
  };
  xhr.open("post", window.location.origin + "/sigma", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.send(JSON.stringify(params));
}

function filterFormatOptions() {
  // clear all elemeents from select
  let select = document.getElementById("select-format");
  let tomSelect = select.tomselect;
  tomSelect.clear();
  tomSelect.clearOptions();

  // only add the formats which match the selected backend
  let backend = getSelectValue("select-backend");
  var options = select.querySelectorAll('option[backend$="' + backend + '"]');
  options = [...options];
  options.forEach((option) => {
    tomSelect.addOption({
      label: option.label,
      value: option.value
    });
  });
  // select the first element
  tomSelect.addItem(options[0].value);
}

function filterPipelineOptions() {
  // clear all elemeents from select
  let select = document.getElementById("select-pipeline");
  let tomSelect = select.tomselect;
  tomSelect.clear();
  tomSelect.clearOptions();

  // only add the pipeplines which match the selected backend or have backend=="all"
  let backend = getSelectValue("select-backend");
  var options = select.querySelectorAll(
    'option[backend$="' + backend + '"], option[backend$=all]'
  );
  options = [...options];
  options.forEach((option) => {
    tomSelect.addOption({
      label: option.label,
      value: option.value
    });
  });
}
