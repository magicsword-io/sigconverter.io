// Initialize select dropdowns
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

new TomSelect("#select-sigma-version", {
  controlInput: null,
  valueField: "value",
  labelField: "label",
  sortField: {
    field: "value",
    direction: "desc"
  }
});

// Initial setup when page loads
window.onload = async function() {
  try {
    // Initialize version selector first
    await updateSigmaVersions();
    // Get the fragment section from the current URL
    const fragment = window.location.hash.substring(1);
    const pairs = fragment.split("&");
    const urlParameter = new Map();
    
    pairs.forEach(function(pair) {
      const [key, value] = pair.split("=");
      if (key && value) {
        urlParameter.set(decodeURIComponent(key), decodeURIComponent(value));
      }
    });
  
    // Handle URL parameters
    if (urlParameter.has("hideEditor")) {
      let hideEditor = urlParameter.get("hideEditor");
      if (hideEditor == 1) {
        document.getElementById("rule-section").style.display = "none";
        document.getElementById("rule-grid").setAttribute("class", "");
      }
    } 
  
    const version = getSelectValue("select-sigma-version");
    if (!version) {
      console.error("No Sigma version selected");
      return;
    }

    // Then update other selectors with the selected version
    await updateTargets(version);
    await updateFormats(version);
    await updatePipelines(version);
    
    // Generate initial CLI and convert
    generateCli();
    await convert(sigmaJar.toString(), pipelineJar.toString());
  } catch (error) {
    console.error("Error during initialization:", error);
  }
};

// Event Listeners
document.getElementById("select-sigma-version").addEventListener("change", async function() {
  try {
    const version = getSelectValue("select-sigma-version");
    if (!version) {
      console.error("No Sigma version selected");
      return;
    }

    // Update all dependent selectors
    await updateTargets(version);
    await updateFormats(version);
    await updatePipelines(version);
    
    // Update UI
    generateCli();
    await convert(sigmaJar.toString(), pipelineJar.toString());
  } catch (error) {
    console.error("Error updating version:", error);
  }
});

document.getElementById("select-backend").addEventListener("change", async function() {
  const version = getSelectValue("select-sigma-version");
  await updateFormats(version);
  await updatePipelines(version);
  updateBackendSyntax();
  generateCli();
  await convert(sigmaJar.toString(), pipelineJar.toString());
});

document.getElementById("select-format").addEventListener("change", function() {
  generateCli();
  convert(sigmaJar.toString(), pipelineJar.toString());
});

document.getElementById("select-pipeline").addEventListener("change", function() {
  generateCli();
  convert(sigmaJar.toString(), pipelineJar.toString());
});

// Button handlers
document.getElementById("query-copy-btn").onclick = function() {
  copyQuery();
};

document.getElementById("rule-share-btn").onclick = function() {
  generateShareLink();
};

document.getElementById("tab-rule").onclick = function() {
  showTab("tab-rule", "rule-code");
};

document.getElementById("tab-pipeline").onclick = function() {
  showTab("tab-pipeline", "pipeline-code");
};

// Utility Functions
function base64Encode(str) {
  return window.btoa(unescape(encodeURIComponent(str)));
}

function base64Decode(str) {
  return decodeURIComponent(escape(window.atob(str)));
}

function getSelectValue(elementId) {
  let select = document.getElementById(elementId);
  let tomSelect = select.tomselect;
  return tomSelect.getValue();
}

function focusSelect(elementId) {
  document.getElementById(elementId).focus();
}

function showTab(tabId, codeId) {
  var i, tabcontent, tablinks;
  var tab = document.getElementById(tabId);
  var code = document.getElementById(codeId);
  
  // Hide all code areas
  tabcontent = document.getElementsByClassName("tab-code");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].classList.add('hidden');
  }

  // Remove color from all tabs
  tablinks = document.getElementsByClassName("file-tab");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].classList.remove('bg-sigma-blue');
    tablinks[i].classList.remove('text-sigma-dark');
  }

  // Display the selected code area
  code.parentElement.classList.remove('hidden');

  // Change color of tab button
  tab.classList.add('bg-sigma-blue');
  tab.classList.add('text-sigma-dark');
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

  setTimeout(function() {
    ruleShareBtn.classList.toggle("text-sigma-blue");
    ruleShareBtn.classList.toggle("text-green-400");
  }, 1200);
}

function generateCli() {
  let cliCode = document.getElementById("cli-code");
  let version = getSelectValue("select-sigma-version");
  let backend = getSelectValue("select-backend");
  let format = getSelectValue("select-format");
  let pipelines = getSelectValue("select-pipeline");

  let cliCommand = `sigma convert -t ${backend} -f ${format}`;
  
  if (Array.isArray(pipelines) && pipelines.length > 0) {
    pipelines.forEach(pipeline => {
      cliCommand += ` -p ${pipeline}`;
    });
  } else if (pipelines) {
    cliCommand += ` -p ${pipelines}`;
  }

  cliCommand += " rule.yml";
  cliCode.innerHTML = cliCommand;
  Prism.highlightElement(cliCode);
}

// API Functions
async function updateSigmaVersions() {
  try {
    const response = await fetch(`${window.location.origin}/api/v1/sigma-versions`);
    const versions = await response.json();

    let select = document.getElementById("select-sigma-version");
    let tomSelect = select.tomselect;
    
    // Clear existing options
    tomSelect.clear(true);
    tomSelect.clearOptions();

    // Add each version as an option
    versions.forEach(version => {
      tomSelect.addOption({
        value: version,
        label: `Sigma ${version}`
      });
    });
    
    // Select the latest version (first in the array)
    if (versions.length > 0) {
      tomSelect.addItem(versions[0]);
    }
  } catch (error) {
    console.error("Error fetching Sigma versions:", error);
  }
}

async function updateTargets(version) {
  try {
    const response = await fetch(`${window.location.origin}/api/v1/${version}/targets`);
    const data = await response.json();

    let select = document.getElementById("select-backend");
    let currentValue = getSelectValue("select-backend");
    let tomSelect = select.tomselect;
    
    tomSelect.clear(true);
    tomSelect.clearOptions();

    if (data.targets) {
      data.targets.forEach(target => {
        tomSelect.addOption({
          value: target,
          label: target
        });
      });
      
      if (data.targets.includes(currentValue)) {
        tomSelect.addItem(currentValue);
      } else {
        const defaultTarget = data.targets.includes('splunk') ? 'splunk' : data.targets[0];
        tomSelect.addItem(defaultTarget);
      }
    }
  } catch (error) {
    console.error("Error fetching targets:", error);
  }
}

async function updateFormats(version) {
  try {
    const backend = getSelectValue("select-backend");
    if (!backend) return;

    const response = await fetch(`${window.location.origin}/api/v1/${version}/formats?target=${encodeURIComponent(backend)}`);
    const data = await response.json();

    let select = document.getElementById("select-format");
    let currentValue = getSelectValue("select-format");
    let tomSelect = select.tomselect;
    
    tomSelect.clear(true);
    tomSelect.clearOptions();

    if (data.formats) {
      data.formats.forEach(format => {
        tomSelect.addOption({
          value: format,
          label: format
        });
      });
      
      if (data.formats.includes(currentValue)) {
        tomSelect.addItem(currentValue);
      } else if (data.formats.length > 0) {
        tomSelect.addItem(data.formats[0]);
      }
    }
  } catch (error) {
    console.error("Error updating formats:", error);
  }
}

async function updatePipelines(version) {
  try {
    const backend = getSelectValue("select-backend");
    if (!backend) return;

    const response = await fetch(`${window.location.origin}/api/v1/${version}/pipelines?target=${encodeURIComponent(backend)}`);
    const data = await response.json();

    let select = document.getElementById("select-pipeline");
    let tomSelect = select.tomselect;
    
    tomSelect.clear(true);
    tomSelect.clearOptions();

    if (data.pipelines) {
      data.pipelines.forEach(pipeline => {
        tomSelect.addOption({
          value: pipeline,
          label: pipeline
        });
      });
    }
  } catch (error) {
    console.error("Error updating pipelines:", error);
  }
}

async function convert(sigmaRule, customPipeline) {
  try {
    const version = getSelectValue("select-sigma-version");
    const backend = getSelectValue("select-backend");
    const format = getSelectValue("select-format");
    const pipelines = getSelectValue("select-pipeline");

    const response = await fetch(`${window.location.origin}/api/v1/${version}/convert`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        rule: base64Encode(sigmaRule),
        target: backend,
        format: format,
        pipeline: Array.isArray(pipelines) ? pipelines : [pipelines]
      })
    });

    const queryCode = document.getElementById("query-code");
    
    if (response.ok) {
      const data = await response.json();
      if (typeof data === 'string') {
        queryCode.value = data;
        queryCode.innerHTML = data;
      } else if (data.queries) {
        queryCode.value = data.queries;
        queryCode.innerHTML = data.queries;
      } else {
        queryCode.value = "No query generated";
        queryCode.innerHTML = "No query generated";
      }
      Prism.highlightElement(queryCode);
    } else {
      const error = await response.text();
      queryCode.value = `Error: ${error}`;
      queryCode.innerHTML = `Error: ${error}`;
    }
  } catch (error) {
    console.error("Conversion error:", error);
    document.getElementById("query-code").value = `Error: ${error.message}`;
  }
}

// Update syntax highlighting based on backend
function updateBackendSyntax() {
  let backend = getSelectValue("select-backend");
  let language = "";
  let prev_language = "";
  let default_language = "language-sql";

  let prev_lang_class = document.getElementById("query-code").classList;
  for (let prev of prev_lang_class) {
    if (prev.match(/^language-\w+(-\w+)?/)) {
      prev_language = prev;
    }
  }

  const languageMap = {
    "azure": "language-kusto",
    "ibm-qradar-aql": "language-sql",
    "microsoft365defender": "language-kusto",
    "splunk": "language-splunk-spl",
    "qradar": "language-sql"
  };

  language = languageMap[backend] ? languageMap[backend] : default_language;

  document.getElementById("query-code").classList.remove(prev_language);
  document.getElementById("query-code").classList.toggle(language);
}

// Update the settings button handlers
document.getElementById("settings-btn").onclick = function() {
  let settingsModal = document.getElementById("settings-modal");
  settingsModal.classList.remove("hidden");
};

document.getElementById("settings-close-btn").onclick = function() {
  let settingsModal = document.getElementById("settings-modal");
  settingsModal.classList.add("hidden");
};

// Update the version selector event handler
document.getElementById("select-sigma-version").onchange = async function() {
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
