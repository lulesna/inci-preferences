async function fetchAllPages(url) {
    let results = [];
    let nextUrl = url;

    while (nextUrl) {
        const response = await fetch(nextUrl);
        const data = await response.json();

        if (Array.isArray(data)) {
            return data;
        }

        results = results.concat(data.results || []);
        nextUrl = data.next;
    }

    return results;
}
