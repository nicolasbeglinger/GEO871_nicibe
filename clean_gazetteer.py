import pandas as pd

def clean_gazetteer(path: str, featureclass: list):

    iter_csv = pd.read_csv(path,
                           delimiter="\t",
                           names=["geonameid", "name", "asciiname", "alternatenames", "latitude", "longitude",
                                  "featureclass", "featurecode", "countrycode", "cc2", "admin1code", "admin2code",
                                  "admin3code", "admin4code", "population", "elevation",
                                  "dem", "timezone", "modificationdate"],
                           iterator=True,
                           chunksize=1000)

    # df = pd.concat([chunk[chunk['featureclass'] in featureclass] for chunk in iter_csv])

    lyst = []

    for i, chunk in enumerate(iter_csv):

        lyst.append(chunk[chunk["featureclass"].isin(featureclass)])
        # if len(lyst) == 1:
        #     break
        if i % 10 == 0:
            print(i)

    df = pd.concat(lyst)


    return df


if __name__ == "__main__":
    world = clean_gazetteer(path="data/geonames/allCountries.txt", featureclass=["A", "T", "P"])
