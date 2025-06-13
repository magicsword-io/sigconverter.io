// initialize select dropdowns
new TomSelect("#select-backend", {
  controlInput: null,
  valueField: "value",
  labelField: "label",
  sortField: {
    field: "value",
    direction: "asc",
  },
});
new TomSelect("#select-format", {
  controlInput: null,
  valueField: "value",
  labelField: "label",
});
new TomSelect("#select-pipeline", {
  allowEmptyOption: true,
  plugins: ["remove_button", "checkbox_options"],
  persist: false,
  hidePlaceholder: true,
  searchField: "value",
  valueField: "value",
  labelField: "label",
});
new TomSelect("#select-sigma-version", {
  controlInput: null,
  valueField: "value",
  labelField: "label",
  sortField: {
    field: "value",
    direction: "desc",
  },
});

// initial stuff todo when page is loaded
window.onload = async function () {
  // load initial data from api
  await updateSigmaVersions();

  // Get the fragment section from the current URL, without the '#' character
  const fragment = window.location.hash.substring(1);

  // Split the hash into key-value pair strings
  const pairs = fragment.split("&");

  // Parse each pair into a key and a value and store them in a map
  const urlParameter = new Map();
  pairs.forEach(function (pair) {
    const [key, value] = pair.split("=");
    // If both key and value are present, decode and store them
    if (key && value) {
      urlParameter.set(decodeURIComponent(key), decodeURIComponent(value));
    }
  });

  // check if hideEditor parameter is in url
  if (urlParameter.has("hideEditor")) {
    let hideEditor = urlParameter.get("hideEditor");
    if (hideEditor == 1) {
      document.getElementById("rule-section").style.display = "none";
      document.getElementById("rule-grid").setAttribute("class", "");
    }
  }

  // check if rule parameter is in url
  if (urlParameter.has("rule")) {
    let rule = base64Decode(urlParameter.get("rule"));
    sigmaJar.updateCode(rule);
  }

  // check if pipelineYml parameter is in url
  if (urlParameter.has("pipelineYml")) {
    let pipelineYml = base64Decode(urlParameter.get("pipelineYml"));
    pipelineJar.updateCode(pipelineYml);
  }

  let versionSelect = document.getElementById("select-sigma-version");
  if (urlParameter.has("version")) {
    versionSelect.tomselect.addItem(urlParameter.get("version"), true);
  }
  let version = getSelectValue("select-sigma-version");

  await updateTargets(version);

  let backendSelect = document.getElementById("select-backend");
  // get parameter backend from url and check if it's a valid option
  if (
    urlParameter.has("backend") &&
    backendSelect.querySelectorAll(
      'option[value$="' + urlParameter.get("backend") + '"]',
    ).length > 0
  ) {
    // select item in dropdown
    backendSelect.tomselect.addItem(urlParameter.get("backend"));
  } else {
    // select splunk backend as default
    backendSelect.tomselect.addItem("splunk");
  }

  await updateFormats(version);
  // only show formats for selected backend
  filterFormatOptions();

  // get parameter format and select item in dropdown
  let formatSelect = document.getElementById("select-format");
  if (urlParameter.has("format")) {
    formatSelect.tomselect.addItem(urlParameter.get("format"));
  }

  await updatePipelines(version);
  // only show pipelines available for selected backend
  filterPipelineOptions();

  let pipelineSelect = document.getElementById("select-pipeline");
  if (urlParameter.has("pipeline")) {
    const pipelineValues = urlParameter.get("pipeline").split(";");
    pipelineValues.forEach(function (value) {
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
  updateBackendSyntax();
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

document.getElementById("select-sigma-version").onchange = async function () {
  let version = getSelectValue("select-sigma-version");
  await updateTargets(version);
  await updateFormats(version);
  await updatePipelines(version);
  updateBackendSyntax();
  filterFormatOptions();
  filterPipelineOptions();
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
document.getElementById("settings-btn").onclick = function () {
  let settingsModal = document.getElementById("settings-modal");
  settingsModal.classList.remove("hidden");
};
document.getElementById("settings-close-btn").onclick = function () {
  let settingsModal = document.getElementById("settings-modal");
  settingsModal.classList.add("hidden");
};

function base64Encode(str) {
  return window.btoa(unescape(encodeURIComponent(str)));
}

function base64Decode(str) {
  return decodeURIComponent(escape(window.atob(str)));
}

function showTab(tabId, codeId) {
  var i, tabcontent, tablinks;
  var tab = document.getElementById(tabId);
  var code = document.getElementById(codeId);

  // hide all code areas
  tabcontent = document.getElementsByClassName("tab-code");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].classList.add("hidden");
  }

  // remove color from all tabs
  tablinks = document.getElementsByClassName("file-tab");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].classList.remove("bg-sigma-blue");
    tablinks[i].classList.remove("text-sigma-dark");
  }

  // display the selected code area
  code.parentElement.classList.remove("hidden");

  // change color of tab button to indicate selected code area
  tab.classList.add("bg-sigma-blue");
  tab.classList.add("text-sigma-dark");
}

function generateShareLink() {
  let version = getSelectValue("select-sigma-version");
  let backend = getSelectValue("select-backend");
  let format = getSelectValue("select-format");
  let pipelines = getSelectValue("select-pipeline");
  let rule = encodeURIComponent(base64Encode(sigmaJar.toString()));
  let pipelineYml = encodeURIComponent(base64Encode(pipelineJar.toString()));

  // generate link with parameters
  let shareParams =
    "#version=" +
    version +
    "&backend=" +
    backend +
    "&format=" +
    format +
    "&pipeline=" +
    pipelines.join(";") +
    "&rule=" +
    rule +
    "&pipelineYml=" +
    pipelineYml;
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
    cliCommand = cliCommand + " --without-pipeline";
  }
  pipelines.forEach((e) => {
    cliCommand = cliCommand + " -p " + e;
  });

  if (pipelineJar.toString().length > 0) {
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
    rule: base64Encode(sigmaRule),
    pipelineYml: base64Encode(customPipeline),
    pipeline: pipelines,
    target: backend,
    format: format,
    html: "true"
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
  let version = getSelectValue("select-sigma-version");
  xhr.open(
    "post",
    window.location.origin + "/api/v1/" + version + "/convert",
    true,
  );
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.send(JSON.stringify(params));
}

function filterFormatOptions() {
  // clear all elements from select
  let select = document.getElementById("select-format");
  let currentValue = getSelectValue("select-format");
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
      value: option.value,
    });
    if (option.value == currentValue) {
      // reselect format if it still exists after filtering
      tomSelect.addItem(currentValue);
    }
  });
  // if nothing is selected chose the first format
  if (tomSelect.items.length == 0) {
    if (options.length > 0) {
      tomSelect.addItem(options[0].value);
    }
  }
}

function filterPipelineOptions() {
  // clear all elements from select
  let select = document.getElementById("select-pipeline");
  let tomSelect = select.tomselect;
  tomSelect.clear();
  tomSelect.clearOptions();

  // only add the pipeplines which match the selected backend or have backend=="all"
  let backend = getSelectValue("select-backend");
  var options = select.querySelectorAll(
    'option[target$="' + backend + '"], option[target=""]',
  );
  options = [...options];
  options.forEach((option) => {
    tomSelect.addOption({
      label: option.label,
      value: option.value,
    });
  });
}

// Updates the query-code code block with a prismjs class mapped to the language
function updateBackendSyntax() {
  let backend = getSelectValue("select-backend");
  let language = "";
  let prev_language = "";
  let default_language = "language-sql";

  // Determines what class was previously present upon a new backend selection
  let prev_lang_class = document.getElementById("query-code").classList;
  for (let prev of prev_lang_class) {
    if (prev.match(/^language-\w+(-\w+)?/)) {
      prev_language = prev;
    }
  }

  const languageMap = {
    azure: "language-kusto",
    "ibm-qradar-aql": "language-sql",
    microsoft365defender: "language-kusto",
    splunk: "language-splunk-spl",
    qradar: "language-sql",
  };

  language = languageMap[backend] ? languageMap[backend] : default_language;

  document.getElementById("query-code").classList.remove(prev_language);
  document.getElementById("query-code").classList.toggle(language);
}

// Update functions that fetch data from the API and populates the dropdowns
async function updateSigmaVersions() {
  try {
    url = window.location.origin + "/api/v1/sigma-versions";
    const response = await fetch(url);
    const data = await response.json();

    let select = document.getElementById("select-sigma-version");
    let tomSelect = select.tomselect;
    // Clear any existing options
    select.innerHTML = "";
    tomSelect.clearOptions();

    data.forEach((item) => {
      tomSelect.addOption({
        label: item,
        value: item,
      });
    });

    // select the first element
    tomSelect.addItem(data[0]);
  } catch (error) {
    console.error("Error fetching data:", error);
  }
}

async function updateTargets(version) {
  try {
    url = window.location.origin + "/api/v1/" + version + "/targets";
    const response = await fetch(url);
    const data = await response.json();

    let select = document.getElementById("select-backend");
    let currentValue = getSelectValue("select-backend");
    let tomSelect = select.tomselect;
    // Clear any existing options
    select.innerHTML = "";
    tomSelect.clear(true);
    tomSelect.clearOptions();

    data.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.name;
      option.textContent = item.name;
      select.appendChild(option);

      tomSelect.addOption({
        label: item.name,
        value: item.name,
      });
      if (item.name == currentValue) {
        // reselect target if it still exists in new version
        tomSelect.addItem(currentValue, true);
      }
    });
    // if nothing is selected chose splunk
    if (tomSelect.items.length == 0) {
      tomSelect.addItem("splunk", true);
    }
  } catch (error) {
    console.error("Error fetching data:", error);
  }
}

async function updateFormats(version) {
  try {
    url = window.location.origin + "/api/v1/" + version + "/formats";
    const response = await fetch(url);
    const data = await response.json();

    let select = document.getElementById("select-format");
    let currentValue = getSelectValue("select-format");
    let tomSelect = select.tomselect;
    // Clear any existing options
    select.innerHTML = "";
    tomSelect.clear(true);
    tomSelect.clearOptions();

    data.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.name;
      option.textContent = item.name;
      option.setAttribute("backend", item.target);
      select.appendChild(option);

      tomSelect.addOption({
        label: item.name,
        value: item.name,
      });
      if (item.name == currentValue) {
        // reselect format if it still exists in new version
        tomSelect.addItem(currentValue, true);
      }
    });

    // if nothing is selected chose the first format
    if (tomSelect.items.length == 0) {
      tomSelect.addItem(data[0].name, true);
    }
  } catch (error) {
    console.error("Error fetching data:", error);
  }
}

async function updatePipelines(version) {
  try {
    url = window.location.origin + "/api/v1/" + version + "/pipelines";
    const response = await fetch(url);
    const data = await response.json();

    let select = document.getElementById("select-pipeline");
    let tomSelect = select.tomselect;
    // Clear any existing options
    select.innerHTML = "";
    tomSelect.clearOptions();

    data.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.name;
      option.textContent = item.name;
      option.setAttribute("target", item.targets);
      select.appendChild(option);

      tomSelect.addOption({
        label: item.name,
        value: item.name,
      });
    });
  } catch (error) {
    console.error("Error fetching data:", error);
  }
}
