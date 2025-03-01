
fetch('http://127.0.0.1/')
  .then((response) => {
    return response.json();
  })
  .then((myJson) => {
    if ('ai' in self && 'translator' in self.ai) {
        // The Translator API is supported.
      }
  });